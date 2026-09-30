-- =============================================================================
-- Contagem de ENTIDADES (conceituais) na base e-SUS APS/PEC — schema public
--
-- Cada tabela física é classificada e, quando faz parte de outra entidade,
-- apontada para a sua "entidade raiz". A contagem final é o número de raízes
-- distintas, e não o número de tabelas.
--
-- Regras, na ordem em que são aplicadas:
--   1. historico_auditoria : ta_* (auditoria), tl_* (revisão/Envers) e
--                            tabelas *historico* — são cópias de outra tabela.
--   2. infraestrutura      : tabelas técnicas do sistema (migração, ETL,
--                            sincronização, lote de transmissão, config, token,
--                            controle de acesso etc.). Lista editável abaixo.
--   3. dw_dimensao         : tb_dim_* — dimensões do DW (lookup, não entidade).
--   4. dw_fato             : tb_fat_* — agrupadas pelo domínio do DW
--                            (ex.: tb_fat_atd_ind_exames -> Atendimento individual).
--   5. associativa         : rl_* — relacionamento N:N entre entidades.
--   6. dominio             : tb_tipo_* ou tabela sem nenhuma FK de saída
--                            (lookup / catálogo de referência).
--   7. extensao_1_1        : PK é também FK para outra tabela (subtipo/1:1)
--                            -> pertence à tabela referenciada.
--   8. dependente          : tem FK para uma tabela cujo nome é prefixo do seu
--                            (tb_alergia_evolucao -> tb_alergia), ou só tem
--                            chaves + no máx. 1 atributo próprio e aponta para
--                            uma única tabela não-domínio (atributo multivalorado)
--                            -> pertence à tabela referenciada.
--   9. entidade            : o que sobrar.
-- =============================================================================

with recursive
tabelas as (
    select t.oid, t.relname::text as tabela, t.relnatts as n_cols
    from pg_class t
    join pg_namespace n on n.oid = t.relnamespace
    where n.nspname = 'public' and t.relkind in ('r', 'p')
),
pk as (
    select conrelid as oid, conkey as pk_cols
    from pg_constraint where contype = 'p'
),
fk as (
    select distinct conrelid as oid, confrelid as alvo, conkey as fk_cols
    from pg_constraint
    where contype = 'f' and conrelid <> confrelid
),
fk_cols as (
    select oid, array_agg(distinct c) as cols
    from fk, unnest(fk_cols) c group by oid
),
feat as (
    select t.*,
           (select count(distinct alvo) from fk where fk.oid = t.oid) as n_fk,
           coalesce(pk.pk_cols <@ fc.cols, false) as pk_e_fk,
           (select count(*) from pg_attribute a
             where a.attrelid = t.oid and a.attnum > 0 and not a.attisdropped
               and not (a.attnum = any (coalesce(pk.pk_cols, '{}')))
               and not (a.attnum = any (coalesce(fc.cols, '{}')))) as n_attr
    from tabelas t
    left join pk on pk.oid = t.oid
    left join fk_cols fc on fc.oid = t.oid
),
-- passo 1: categorias que não dependem de outras tabelas -----------------------
cat1 as (
    select f.*,
        case
            when tabela ~ '^(ta|tl)_' or tabela ~ 'historico'
                then 'historico_auditoria'
            when lower(tabela) ~ ('^(spring_'
                  '|tb_migracao|tb_etl_|tb_report_|tb_rel_fichas_config|tb_dado_rel_'
                  '|tb_config|tb_cfg_|tb_servidor_smtp|tb_certificado'
                  '|tb_refresh_token|tb_token_|tb_revisao$|tb_auditoria_'
                  '|tb_envio_|tb_lote_transp|tb_nodo|tb_situacao_lote_transp'
                  '|tb_recebimento_|tb_dado_recebido|tb_dado_transp|tb_pedido_envio'
                  '|tb_processamento_|tb_relatorio_processamento'
                  '|tb_credencial_integracao|tb_recurso|tb_sistema_externo|tb_integracao_'
                  '|tb_unificacao_base|tb_.*_unif(icacao)?_base'
                  '|tb_ad_sync_entity|tb_ad_transmissao_sessao|tb_sessao_sincronizacao'
                  '|tb_importacao_|tb_arquivo_temporario|tb_rascunho_'
                  '|tb_ator|tb_perfil|tb_usuario|tb_ativacao_agendamento_online'
                  '|tb_dispositivo_painel|tb_chamada_painel'
                  '|tb_notificacao_status|tb_topico_notificacao|tb_territorio_.*_erro'
                  '|tb_acomp_cidadaos_vinc)')
                then 'infraestrutura'
            when tabela like 'tb\_dim\_%' then 'dw_dimensao'
            when tabela like 'tb\_fat\_%' then 'dw_fato'
            when tabela like 'rl\_%'      then 'associativa'
            when tabela like 'tb\_tipo\_%' or n_fk = 0 then 'dominio'
        end as cat
    from feat f
),
-- passo 2: extensão / dependente apontam para um pai não-domínio ---------------
pai as (
    select c.oid,
        coalesce(
            -- 7. PK = FK (1:1)
            (select p.oid from fk join pk on pk.oid = c.oid join cat1 p on p.oid = fk.alvo
              where fk.oid = c.oid and c.pk_e_fk and fk.fk_cols && pk.pk_cols
              order by length(p.tabela) desc limit 1),
            -- 8a. FK para tabela cujo nome é prefixo do nome desta
            (select p.oid from fk join cat1 p on p.oid = fk.alvo
              where fk.oid = c.oid and c.tabela like p.tabela || '\_%'
                and coalesce(p.cat, 'x') not in ('dominio', 'historico_auditoria')
              order by length(p.tabela) desc limit 1),
            -- 8b. só chaves + <=1 atributo, apontando para uma única tabela não-domínio
            (select min(p.oid::bigint)::oid from fk join cat1 p on p.oid = fk.alvo
              where fk.oid = c.oid and c.n_attr <= 1 and p.cat is null
              having count(distinct p.oid) = 1)
        ) as pai_oid,
        case when c.pk_e_fk then 'extensao_1_1' else 'dependente' end as cat_pai
    from cat1 c
    where c.cat is null
),
classif as (
    select c.oid, c.tabela, c.n_cols, c.n_fk, c.n_attr,
           coalesce(c.cat, case when p.pai_oid is not null then p.cat_pai else 'entidade' end) as categoria,
           p.pai_oid
    from cat1 c left join pai p on p.oid = c.oid
),
-- passo 3: sobe a cadeia de pais até a entidade raiz ---------------------------
raiz(oid, atual, nivel) as (
    select oid, oid, 0 from classif
    union all
    select r.oid, c.pai_oid, r.nivel + 1
    from raiz r join classif c on c.oid = r.atual
    where c.pai_oid is not null and r.nivel < 20
),
raiz_final as (
    select distinct on (oid) oid, atual as raiz_oid
    from raiz order by oid, nivel desc
),
-- passo 4: domínio do DW (as fatos-filhas não têm FK para a fato-pai) ---------
dw as (
    select oid,
        case
            when tabela ~ '^tb_fat_(cidadao|cidadao_pec|cidadao_territorio)$'          then 'DW: Cidadão'
            when tabela ~ '^tb_fat_familia'                                            then 'DW: Família'
            when tabela ~ '^tb_fat_(cad_individual|cidadao_aldeado|consolidado_cidadao_fci)' then 'DW: Cadastro individual'
            when tabela ~ '^tb_fat_cad_dom'                                            then 'DW: Cadastro domiciliar'
            when tabela ~ '^tb_fat_(atendimento_individual|atd_ind_|consolidado_cidadao_fai|cnslddo_ciddo_fai)' then 'DW: Atendimento individual'
            when tabela ~ '^tb_fat_(atendimento_odonto|atend_odonto_|consolidado_cidadao_fao)' then 'DW: Atendimento odontológico'
            when tabela ~ '^tb_fat_(atendimento_domiciliar|atend_dom_|consolidado_cidadao_fad)' then 'DW: Atendimento domiciliar'
            when tabela ~ '^tb_fat_(atividade_coletiva|atvdd_coletiva)'                 then 'DW: Atividade coletiva'
            when tabela ~ '^tb_fat_(proced|consolidado_cidadao_fp$)'                   then 'DW: Procedimentos'
            when tabela ~ '^tb_fat_(visita_domiciliar|consolidado_cidadao_fvd)'        then 'DW: Visita domiciliar'
            when tabela ~ '^tb_fat_marca_consumo'                                      then 'DW: Marcadores de consumo alimentar'
            when tabela ~ '^tb_fat_avaliacao_elegibilidade'                           then 'DW: Avaliação de elegibilidade'
            when tabela ~ '^tb_fat_complementar'                                       then 'DW: Zika/Microcefalia (complementar)'
            when tabela ~ '^tb_fat_vacinacao'                                          then 'DW: Vacinação'
            when tabela ~ '^tb_fat_cuidado_compartilhado'                              then 'DW: Cuidado compartilhado'
            when tabela ~ '^tb_fat_ivcf'                                               then 'DW: IVCF-20'
            when tabela ~ '^tb_fat_(rel_op_|op_acompanhamento)'                        then 'DW: Relatórios operacionais'
            when tabela ~ '^tb_fat_app_atendimento'                                    then 'DW: Atendimento via app'
            when tabela ~ '^tb_fat_solicitacao_oci'                                    then 'DW: Solicitação OCI'
            when tabela ~ '^tb_fat_fichas'                                             then 'DW: Fichas (controle)'
            else 'DW: ' || tabela
        end as dominio
    from classif where categoria = 'dw_fato'
),
resultado as (
    select c.tabela,
           case when c.categoria like 'dw\_%' then 'DW' else 'Operacional' end as camada,
           -- extensão/dependente de uma tabela de infraestrutura/domínio herda a categoria dela
           case when rc.categoria in ('infraestrutura', 'dominio') then rc.categoria
                else c.categoria end as categoria,
           case when dw.dominio is not null then dw.dominio
                when rc.categoria = 'entidade' then rc.tabela end as entidade,
           c.n_cols, c.n_fk, c.n_attr
    from classif c
    left join raiz_final rf on rf.oid = c.oid
    left join classif rc on rc.oid = rf.raiz_oid
    left join dw on dw.oid = c.oid
)

-- ============================ ESCOLHA UMA SAÍDA ==============================

-- (A) Resumo: tabelas vs entidades por camada/categoria
select camada, categoria,
       count(*)                 as n_tabelas,
       count(distinct entidade) as n_entidades
from resultado
group by rollup (camada, categoria)
order by camada nulls last, categoria nulls last;

-- (B) Lista de entidades e quantas tabelas compõem cada uma
-- select camada, entidade, count(*) as n_tabelas,
--        string_agg(tabela, ', ' order by tabela) as tabelas
-- from resultado
-- where entidade is not null
-- group by camada, entidade
-- order by camada, entidade;

-- (C) Classificação tabela a tabela (para auditar/ajustar as regras)
-- select * from resultado order by camada, categoria, entidade, tabela;
