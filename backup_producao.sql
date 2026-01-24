--
-- PostgreSQL database dump
--

\restrict 4PkALt41hGrRjEhzBKaEl3y9aTLF3uOJJR4tedobnS5aCYcoKwlazIBXCs2NKTL

-- Dumped from database version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: correlatorio; Type: TYPE; Schema: public; Owner: qualigestor
--

CREATE TYPE public.correlatorio AS ENUM (
    'AZUL',
    'VERDE',
    'VERMELHO',
    'LARANJA',
    'ROXO',
    'CINZA'
);


ALTER TYPE public.correlatorio OWNER TO qualigestor;

--
-- Name: modoexibicaonota; Type: TYPE; Schema: public; Owner: qualigestor
--

CREATE TYPE public.modoexibicaonota AS ENUM (
    'PERCENTUAL',
    'PONTOS',
    'AMBOS',
    'OCULTAR'
);


ALTER TYPE public.modoexibicaonota OWNER TO qualigestor;

--
-- Name: statusaplicacao; Type: TYPE; Schema: public; Owner: qualigestor
--

CREATE TYPE public.statusaplicacao AS ENUM (
    'EM_ANDAMENTO',
    'FINALIZADA',
    'CANCELADA',
    'PAUSADA'
);


ALTER TYPE public.statusaplicacao OWNER TO qualigestor;

--
-- Name: statusquestionario; Type: TYPE; Schema: public; Owner: qualigestor
--

CREATE TYPE public.statusquestionario AS ENUM (
    'RASCUNHO',
    'PUBLICADO',
    'ARQUIVADO',
    'INATIVO'
);


ALTER TYPE public.statusquestionario OWNER TO qualigestor;

--
-- Name: tipopreenchimento; Type: TYPE; Schema: public; Owner: qualigestor
--

CREATE TYPE public.tipopreenchimento AS ENUM (
    'RAPIDO',
    'DETALHADO',
    'COMPLETO'
);


ALTER TYPE public.tipopreenchimento OWNER TO qualigestor;

--
-- Name: tiporesposta; Type: TYPE; Schema: public; Owner: qualigestor
--

CREATE TYPE public.tiporesposta AS ENUM (
    'SIM_NAO_NA',
    'MULTIPLA_ESCOLHA',
    'ESCALA_NUMERICA',
    'NOTA',
    'TEXTO_CURTO',
    'TEXTO_LONGO',
    'FOTO',
    'DATA',
    'HORA',
    'NUMERO',
    'PORCENTAGEM',
    'MOEDA',
    'ASSINATURA'
);


ALTER TYPE public.tiporesposta OWNER TO qualigestor;

--
-- Name: tipousuario; Type: TYPE; Schema: public; Owner: qualigestor
--

CREATE TYPE public.tipousuario AS ENUM (
    'SUPER_ADMIN',
    'ADMIN',
    'GESTOR',
    'AUDITOR',
    'USUARIO',
    'VISUALIZADOR'
);


ALTER TYPE public.tipousuario OWNER TO qualigestor;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: qualigestor
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO qualigestor;

--
-- Name: aplicacao_questionario; Type: TABLE; Schema: public; Owner: qualigestor
--

CREATE TABLE public.aplicacao_questionario (
    id integer NOT NULL,
    data_inicio timestamp without time zone NOT NULL,
    data_fim timestamp without time zone,
    status public.statusaplicacao,
    nota_final double precision,
    pontos_obtidos double precision,
    pontos_totais double precision,
    observacoes text,
    observacoes_finais text,
    latitude character varying(50),
    longitude character varying(50),
    endereco_capturado character varying(255),
    questionario_id integer NOT NULL,
    avaliado_id integer NOT NULL,
    aplicador_id integer NOT NULL,
    assinatura_imagem character varying(255),
    assinatura_responsavel character varying(200),
    cargo_responsavel character varying(100)
);


ALTER TABLE public.aplicacao_questionario OWNER TO qualigestor;

--
-- Name: aplicacao_questionario_id_seq; Type: SEQUENCE; Schema: public; Owner: qualigestor
--

CREATE SEQUENCE public.aplicacao_questionario_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.aplicacao_questionario_id_seq OWNER TO qualigestor;

--
-- Name: aplicacao_questionario_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: qualigestor
--

ALTER SEQUENCE public.aplicacao_questionario_id_seq OWNED BY public.aplicacao_questionario.id;


--
-- Name: avaliado; Type: TABLE; Schema: public; Owner: qualigestor
--

CREATE TABLE public.avaliado (
    id integer NOT NULL,
    codigo character varying(20),
    nome character varying(100) NOT NULL,
    endereco character varying(255),
    cidade character varying(100),
    estado character varying(2),
    cep character varying(9),
    telefone character varying(20),
    email character varying(120),
    responsavel character varying(100),
    campos_personalizados text,
    ativo boolean,
    cliente_id integer NOT NULL,
    grupo_id integer,
    criado_em timestamp without time zone,
    atualizado_em timestamp without time zone
);


ALTER TABLE public.avaliado OWNER TO qualigestor;

--
-- Name: avaliado_id_seq; Type: SEQUENCE; Schema: public; Owner: qualigestor
--

CREATE SEQUENCE public.avaliado_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.avaliado_id_seq OWNER TO qualigestor;

--
-- Name: avaliado_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: qualigestor
--

ALTER SEQUENCE public.avaliado_id_seq OWNED BY public.avaliado.id;


--
-- Name: categoria_indicador; Type: TABLE; Schema: public; Owner: qualigestor
--

CREATE TABLE public.categoria_indicador (
    id integer NOT NULL,
    nome character varying(100) NOT NULL,
    ordem integer,
    cor character varying(7),
    ativo boolean,
    cliente_id integer NOT NULL
);


ALTER TABLE public.categoria_indicador OWNER TO qualigestor;

--
-- Name: categoria_indicador_id_seq; Type: SEQUENCE; Schema: public; Owner: qualigestor
--

CREATE SEQUENCE public.categoria_indicador_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categoria_indicador_id_seq OWNER TO qualigestor;

--
-- Name: categoria_indicador_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: qualigestor
--

ALTER SEQUENCE public.categoria_indicador_id_seq OWNED BY public.categoria_indicador.id;


--
-- Name: cliente; Type: TABLE; Schema: public; Owner: qualigestor
--

CREATE TABLE public.cliente (
    id integer NOT NULL,
    nome character varying(200) NOT NULL,
    razao_social character varying(200),
    cnpj character varying(18),
    email character varying(120),
    telefone character varying(20),
    endereco character varying(255),
    ativo boolean,
    criado_em timestamp without time zone,
    plano character varying(50),
    limite_usuarios integer,
    limite_questionarios integer
);


ALTER TABLE public.cliente OWNER TO qualigestor;

--
-- Name: cliente_id_seq; Type: SEQUENCE; Schema: public; Owner: qualigestor
--

CREATE SEQUENCE public.cliente_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cliente_id_seq OWNER TO qualigestor;

--
-- Name: cliente_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: qualigestor
--

ALTER SEQUENCE public.cliente_id_seq OWNED BY public.cliente.id;


--
-- Name: configuracao_cliente; Type: TABLE; Schema: public; Owner: qualigestor
--

CREATE TABLE public.configuracao_cliente (
    id integer NOT NULL,
    logo_url character varying(255),
    cor_primaria character varying(7),
    cor_secundaria character varying(7),
    mostrar_notas boolean,
    permitir_fotos boolean,
    obrigar_plano_acao boolean,
    notificar_aplicacoes_finalizadas boolean,
    notificar_nao_conformidades boolean,
    cliente_id integer NOT NULL,
    criado_em timestamp without time zone,
    atualizado_em timestamp without time zone
);


ALTER TABLE public.configuracao_cliente OWNER TO qualigestor;

--
-- Name: configuracao_cliente_id_seq; Type: SEQUENCE; Schema: public; Owner: qualigestor
--

CREATE SEQUENCE public.configuracao_cliente_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.configuracao_cliente_id_seq OWNER TO qualigestor;

--
-- Name: configuracao_cliente_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: qualigestor
--

ALTER SEQUENCE public.configuracao_cliente_id_seq OWNED BY public.configuracao_cliente.id;


--
-- Name: foto_resposta; Type: TABLE; Schema: public; Owner: qualigestor
--

CREATE TABLE public.foto_resposta (
    id integer NOT NULL,
    caminho character varying(255) NOT NULL,
    data_upload timestamp without time zone,
    resposta_id integer NOT NULL,
    tipo character varying(20) DEFAULT 'evidencia'::character varying
);


ALTER TABLE public.foto_resposta OWNER TO qualigestor;

--
-- Name: foto_resposta_id_seq; Type: SEQUENCE; Schema: public; Owner: qualigestor
--

CREATE SEQUENCE public.foto_resposta_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.foto_resposta_id_seq OWNER TO qualigestor;

--
-- Name: foto_resposta_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: qualigestor
--

ALTER SEQUENCE public.foto_resposta_id_seq OWNED BY public.foto_resposta.id;


--
-- Name: grupo; Type: TABLE; Schema: public; Owner: qualigestor
--

CREATE TABLE public.grupo (
    id integer NOT NULL,
    nome character varying(120) NOT NULL,
    descricao text,
    cliente_id integer NOT NULL,
    ativo boolean,
    criado_em timestamp without time zone
);


ALTER TABLE public.grupo OWNER TO qualigestor;

--
-- Name: grupo_id_seq; Type: SEQUENCE; Schema: public; Owner: qualigestor
--

CREATE SEQUENCE public.grupo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.grupo_id_seq OWNER TO qualigestor;

--
-- Name: grupo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: qualigestor
--

ALTER SEQUENCE public.grupo_id_seq OWNED BY public.grupo.id;


--
-- Name: integracao; Type: TABLE; Schema: public; Owner: qualigestor
--

CREATE TABLE public.integracao (
    id integer NOT NULL,
    nome character varying(100) NOT NULL,
    descricao text,
    tipo character varying(50),
    configuracao text,
    ativa boolean,
    criado_em timestamp without time zone
);


ALTER TABLE public.integracao OWNER TO qualigestor;

--
-- Name: integracao_id_seq; Type: SEQUENCE; Schema: public; Owner: qualigestor
--

CREATE SEQUENCE public.integracao_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.integracao_id_seq OWNER TO qualigestor;

--
-- Name: integracao_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: qualigestor
--

ALTER SEQUENCE public.integracao_id_seq OWNED BY public.integracao.id;


--
-- Name: log_auditoria; Type: TABLE; Schema: public; Owner: qualigestor
--

CREATE TABLE public.log_auditoria (
    id integer NOT NULL,
    acao character varying(200) NOT NULL,
    detalhes text,
    entidade_tipo character varying(50),
    entidade_id integer,
    ip character varying(45),
    user_agent text,
    usuario_id integer NOT NULL,
    cliente_id integer NOT NULL,
    data_acao timestamp without time zone
);


ALTER TABLE public.log_auditoria OWNER TO qualigestor;

--
-- Name: log_auditoria_id_seq; Type: SEQUENCE; Schema: public; Owner: qualigestor
--

CREATE SEQUENCE public.log_auditoria_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.log_auditoria_id_seq OWNER TO qualigestor;

--
-- Name: log_auditoria_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: qualigestor
--

ALTER SEQUENCE public.log_auditoria_id_seq OWNED BY public.log_auditoria.id;


--
-- Name: notificacao; Type: TABLE; Schema: public; Owner: qualigestor
--

CREATE TABLE public.notificacao (
    id integer NOT NULL,
    titulo character varying(200) NOT NULL,
    mensagem text NOT NULL,
    tipo character varying(20),
    link character varying(255),
    visualizada boolean,
    data_visualizacao timestamp without time zone,
    usuario_id integer NOT NULL,
    data_criacao timestamp without time zone
);


ALTER TABLE public.notificacao OWNER TO qualigestor;

--
-- Name: notificacao_id_seq; Type: SEQUENCE; Schema: public; Owner: qualigestor
--

CREATE SEQUENCE public.notificacao_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notificacao_id_seq OWNER TO qualigestor;

--
-- Name: notificacao_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: qualigestor
--

ALTER SEQUENCE public.notificacao_id_seq OWNED BY public.notificacao.id;


--
-- Name: opcao_pergunta; Type: TABLE; Schema: public; Owner: qualigestor
--

CREATE TABLE public.opcao_pergunta (
    id integer NOT NULL,
    texto character varying(200) NOT NULL,
    valor double precision,
    ordem integer NOT NULL,
    ativo boolean,
    pergunta_id integer NOT NULL
);


ALTER TABLE public.opcao_pergunta OWNER TO qualigestor;

--
-- Name: opcao_pergunta_id_seq; Type: SEQUENCE; Schema: public; Owner: qualigestor
--

CREATE SEQUENCE public.opcao_pergunta_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.opcao_pergunta_id_seq OWNER TO qualigestor;

--
-- Name: opcao_pergunta_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: qualigestor
--

ALTER SEQUENCE public.opcao_pergunta_id_seq OWNED BY public.opcao_pergunta.id;


--
-- Name: pergunta; Type: TABLE; Schema: public; Owner: qualigestor
--

CREATE TABLE public.pergunta (
    id integer NOT NULL,
    texto text NOT NULL,
    tipo public.tiporesposta NOT NULL,
    obrigatoria boolean,
    permite_observacao boolean,
    peso integer,
    ordem integer NOT NULL,
    ativo boolean,
    exige_foto_se_nao_conforme boolean NOT NULL,
    configuracoes text,
    topico_id integer NOT NULL,
    criado_em timestamp without time zone,
    criterio_foto character varying(20) DEFAULT 'nenhuma'::character varying
);


ALTER TABLE public.pergunta OWNER TO qualigestor;

--
-- Name: pergunta_id_seq; Type: SEQUENCE; Schema: public; Owner: qualigestor
--

CREATE SEQUENCE public.pergunta_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pergunta_id_seq OWNER TO qualigestor;

--
-- Name: pergunta_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: qualigestor
--

ALTER SEQUENCE public.pergunta_id_seq OWNED BY public.pergunta.id;


--
-- Name: questionario; Type: TABLE; Schema: public; Owner: qualigestor
--

CREATE TABLE public.questionario (
    id integer NOT NULL,
    nome character varying(200) NOT NULL,
    descricao text,
    versao character varying(20),
    modo character varying(50),
    documento_referencia character varying(255),
    calcular_nota boolean,
    ocultar_nota_aplicacao boolean,
    base_calculo integer,
    casas_decimais integer,
    modo_configuracao character varying(20),
    modo_exibicao_nota public.modoexibicaonota,
    anexar_documentos boolean,
    capturar_geolocalizacao boolean,
    restringir_avaliados boolean,
    habilitar_reincidencia boolean,
    tipo_preenchimento public.tipopreenchimento,
    pontuacao_ativa boolean,
    exibir_nota_anterior boolean,
    exibir_tabela_resumo boolean,
    exibir_limites_aceitaveis boolean,
    exibir_data_hora boolean,
    exibir_questoes_omitidas boolean,
    exibir_nao_conformidade boolean,
    cor_relatorio public.correlatorio,
    incluir_assinatura boolean,
    incluir_foto_capa boolean,
    agrupamento_fotos character varying(20),
    ativo boolean,
    publicado boolean,
    status public.statusquestionario,
    cliente_id integer NOT NULL,
    criado_por_id integer NOT NULL,
    criado_em timestamp without time zone,
    atualizado_em timestamp without time zone,
    data_publicacao timestamp without time zone
);


ALTER TABLE public.questionario OWNER TO qualigestor;

--
-- Name: questionario_id_seq; Type: SEQUENCE; Schema: public; Owner: qualigestor
--

CREATE SEQUENCE public.questionario_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.questionario_id_seq OWNER TO qualigestor;

--
-- Name: questionario_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: qualigestor
--

ALTER SEQUENCE public.questionario_id_seq OWNED BY public.questionario.id;


--
-- Name: resposta_pergunta; Type: TABLE; Schema: public; Owner: qualigestor
--

CREATE TABLE public.resposta_pergunta (
    id integer NOT NULL,
    resposta text,
    observacao text,
    pontos double precision,
    caminho_foto character varying(255),
    data_resposta timestamp without time zone,
    tempo_resposta integer,
    nao_conforme boolean,
    plano_acao text,
    prazo_plano_acao date,
    responsavel_plano_acao character varying(100),
    aplicacao_id integer NOT NULL,
    pergunta_id integer NOT NULL,
    status_acao character varying(20) DEFAULT 'pendente'::character varying,
    acao_realizada text,
    data_conclusao timestamp without time zone
);


ALTER TABLE public.resposta_pergunta OWNER TO qualigestor;

--
-- Name: resposta_pergunta_id_seq; Type: SEQUENCE; Schema: public; Owner: qualigestor
--

CREATE SEQUENCE public.resposta_pergunta_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.resposta_pergunta_id_seq OWNER TO qualigestor;

--
-- Name: resposta_pergunta_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: qualigestor
--

ALTER SEQUENCE public.resposta_pergunta_id_seq OWNED BY public.resposta_pergunta.id;


--
-- Name: topico; Type: TABLE; Schema: public; Owner: qualigestor
--

CREATE TABLE public.topico (
    id integer NOT NULL,
    nome character varying(200) NOT NULL,
    descricao text,
    ordem integer,
    ativo boolean,
    questionario_id integer NOT NULL,
    categoria_indicador_id integer
);


ALTER TABLE public.topico OWNER TO qualigestor;

--
-- Name: topico_id_seq; Type: SEQUENCE; Schema: public; Owner: qualigestor
--

CREATE SEQUENCE public.topico_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.topico_id_seq OWNER TO qualigestor;

--
-- Name: topico_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: qualigestor
--

ALTER SEQUENCE public.topico_id_seq OWNED BY public.topico.id;


--
-- Name: usuario; Type: TABLE; Schema: public; Owner: qualigestor
--

CREATE TABLE public.usuario (
    id integer NOT NULL,
    nome character varying(100) NOT NULL,
    email character varying(120) NOT NULL,
    senha_hash character varying(200) NOT NULL,
    telefone character varying(20),
    tipo public.tipousuario NOT NULL,
    ativo boolean,
    ultimo_acesso timestamp without time zone,
    cliente_id integer NOT NULL,
    grupo_id integer,
    avaliado_id integer,
    criado_em timestamp without time zone
);


ALTER TABLE public.usuario OWNER TO qualigestor;

--
-- Name: usuario_autorizado; Type: TABLE; Schema: public; Owner: qualigestor
--

CREATE TABLE public.usuario_autorizado (
    id integer NOT NULL,
    questionario_id integer NOT NULL,
    usuario_id integer NOT NULL,
    criado_em timestamp without time zone
);


ALTER TABLE public.usuario_autorizado OWNER TO qualigestor;

--
-- Name: usuario_autorizado_id_seq; Type: SEQUENCE; Schema: public; Owner: qualigestor
--

CREATE SEQUENCE public.usuario_autorizado_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuario_autorizado_id_seq OWNER TO qualigestor;

--
-- Name: usuario_autorizado_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: qualigestor
--

ALTER SEQUENCE public.usuario_autorizado_id_seq OWNED BY public.usuario_autorizado.id;


--
-- Name: usuario_id_seq; Type: SEQUENCE; Schema: public; Owner: qualigestor
--

CREATE SEQUENCE public.usuario_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuario_id_seq OWNER TO qualigestor;

--
-- Name: usuario_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: qualigestor
--

ALTER SEQUENCE public.usuario_id_seq OWNED BY public.usuario.id;


--
-- Name: aplicacao_questionario id; Type: DEFAULT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.aplicacao_questionario ALTER COLUMN id SET DEFAULT nextval('public.aplicacao_questionario_id_seq'::regclass);


--
-- Name: avaliado id; Type: DEFAULT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.avaliado ALTER COLUMN id SET DEFAULT nextval('public.avaliado_id_seq'::regclass);


--
-- Name: categoria_indicador id; Type: DEFAULT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.categoria_indicador ALTER COLUMN id SET DEFAULT nextval('public.categoria_indicador_id_seq'::regclass);


--
-- Name: cliente id; Type: DEFAULT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.cliente ALTER COLUMN id SET DEFAULT nextval('public.cliente_id_seq'::regclass);


--
-- Name: configuracao_cliente id; Type: DEFAULT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.configuracao_cliente ALTER COLUMN id SET DEFAULT nextval('public.configuracao_cliente_id_seq'::regclass);


--
-- Name: foto_resposta id; Type: DEFAULT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.foto_resposta ALTER COLUMN id SET DEFAULT nextval('public.foto_resposta_id_seq'::regclass);


--
-- Name: grupo id; Type: DEFAULT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.grupo ALTER COLUMN id SET DEFAULT nextval('public.grupo_id_seq'::regclass);


--
-- Name: integracao id; Type: DEFAULT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.integracao ALTER COLUMN id SET DEFAULT nextval('public.integracao_id_seq'::regclass);


--
-- Name: log_auditoria id; Type: DEFAULT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.log_auditoria ALTER COLUMN id SET DEFAULT nextval('public.log_auditoria_id_seq'::regclass);


--
-- Name: notificacao id; Type: DEFAULT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.notificacao ALTER COLUMN id SET DEFAULT nextval('public.notificacao_id_seq'::regclass);


--
-- Name: opcao_pergunta id; Type: DEFAULT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.opcao_pergunta ALTER COLUMN id SET DEFAULT nextval('public.opcao_pergunta_id_seq'::regclass);


--
-- Name: pergunta id; Type: DEFAULT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.pergunta ALTER COLUMN id SET DEFAULT nextval('public.pergunta_id_seq'::regclass);


--
-- Name: questionario id; Type: DEFAULT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.questionario ALTER COLUMN id SET DEFAULT nextval('public.questionario_id_seq'::regclass);


--
-- Name: resposta_pergunta id; Type: DEFAULT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.resposta_pergunta ALTER COLUMN id SET DEFAULT nextval('public.resposta_pergunta_id_seq'::regclass);


--
-- Name: topico id; Type: DEFAULT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.topico ALTER COLUMN id SET DEFAULT nextval('public.topico_id_seq'::regclass);


--
-- Name: usuario id; Type: DEFAULT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.usuario ALTER COLUMN id SET DEFAULT nextval('public.usuario_id_seq'::regclass);


--
-- Name: usuario_autorizado id; Type: DEFAULT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.usuario_autorizado ALTER COLUMN id SET DEFAULT nextval('public.usuario_autorizado_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: qualigestor
--

COPY public.alembic_version (version_num) FROM stdin;
f398b593099f
\.


--
-- Data for Name: aplicacao_questionario; Type: TABLE DATA; Schema: public; Owner: qualigestor
--

COPY public.aplicacao_questionario (id, data_inicio, data_fim, status, nota_final, pontos_obtidos, pontos_totais, observacoes, observacoes_finais, latitude, longitude, endereco_capturado, questionario_id, avaliado_id, aplicador_id, assinatura_imagem, assinatura_responsavel, cargo_responsavel) FROM stdin;
10	2026-01-17 04:33:39.586258	\N	EM_ANDAMENTO	66.67	2	3	\N		\N	\N	\N	3	154	3	\N	\N	\N
11	2026-01-17 23:38:13.823931	\N	EM_ANDAMENTO	\N	\N	\N	\N	\N	\N	\N	\N	3	94	3	\N	\N	\N
12	2026-01-17 23:39:17.198816	\N	EM_ANDAMENTO	\N	\N	\N	\N	\N	\N	\N	\N	2	94	3	\N	\N	\N
13	2026-01-17 23:46:23.249358	\N	EM_ANDAMENTO	\N	\N	\N	\N	\N	\N	\N	\N	3	94	3	\N	\N	\N
14	2026-01-19 00:54:18.904513	\N	EM_ANDAMENTO	\N	\N	\N	\N	\N	\N	\N	\N	2	135	10	\N	\N	\N
17	2026-01-22 12:48:15.421174	\N	EM_ANDAMENTO	\N	\N	\N	\N	\N	\N	\N	\N	2	149	3	\N	\N	\N
18	2026-01-22 12:48:20.249191	\N	EM_ANDAMENTO	\N	\N	\N	\N	\N	\N	\N	\N	2	149	3	\N	\N	\N
19	2026-01-22 13:01:11.420189	\N	EM_ANDAMENTO	\N	\N	\N	\N	\N	\N	\N	\N	2	148	3	\N	\N	\N
20	2026-01-22 20:21:55.409382	\N	EM_ANDAMENTO	\N	\N	\N	\N	\N	\N	\N	\N	2	136	2	\N	\N	\N
21	2026-01-23 17:07:02.752815	\N	EM_ANDAMENTO	\N	\N	\N	\N	\N	\N	\N	\N	2	150	3	\N	\N	\N
22	2026-01-23 20:30:40.474343	\N	EM_ANDAMENTO	\N	\N	\N	\N	\N	\N	\N	\N	2	116	23	\N	\N	\N
23	2026-01-24 02:16:46.020196	\N	EM_ANDAMENTO	\N	\N	\N	\N	\N	\N	\N	\N	2	111	16	\N	\N	\N
15	2026-01-19 00:55:22.794714	2026-01-24 04:08:18.414626	FINALIZADA	88.1	111	126	\N		\N	\N	\N	2	135	10	\N	\N	\N
24	2026-01-24 13:20:10.752668	\N	EM_ANDAMENTO	\N	\N	\N	\N	\N	\N	\N	\N	3	154	3	\N	\N	\N
\.


--
-- Data for Name: avaliado; Type: TABLE DATA; Schema: public; Owner: qualigestor
--

COPY public.avaliado (id, codigo, nome, endereco, cidade, estado, cep, telefone, email, responsavel, campos_personalizados, ativo, cliente_id, grupo_id, criado_em, atualizado_em) FROM stdin;
154	\N	Teste de desenvolvimento	\N	\N	\N	\N	\N	\N	\N	\N	t	2	86	2026-01-17 04:32:03.242557	2026-01-17 04:33:24.830104
153	\N	DIRAD	Rua Coronel Laurênio Lago, S/N - Marechal Hermes CEP: 21610-280 - Rio de Janeiro-RJ	\N	\N	\N	\N	\N	\N	\N	t	2	57	2026-01-08 17:14:18.245663	2026-01-23 19:27:42.413489
96	\N	Rancho DIRAD	Rua Coronel Laurênio Lago, S/N - Marechal Hermes	Rio de Janeiro	RJ	\N	\N	\N	\N	\N	f	2	56	2026-01-08 16:41:53.334355	2026-01-08 17:02:40.410525
93	\N	Rancho HCA	Rua Barão de Itapagipe, 167 - Rio Comprido	Rio de Janeiro	RJ	\N	\N	\N	\N	\N	t	2	56	2026-01-08 16:41:53.334341	2026-01-08 16:41:53.334347
94	\N	Rancho GAP-RJ (DECEA)	Praça Marechal Âncora, 77 – Castelo	Rio de Janeiro	RJ	\N	\N	\N	\N	\N	t	2	56	2026-01-08 16:41:53.334349	2026-01-08 16:41:53.334351
95	\N	Rancho PAME-RJ	Rua General Gurjão, 4 – Caju	Rio de Janeiro	RJ	\N	\N	\N	\N	\N	t	2	56	2026-01-08 16:41:53.334352	2026-01-08 16:41:53.334354
97	\N	Rancho BAAF	Av. Marechal Fontenelle, 1000 - Campo dos Afonsos	Rio de Janeiro	RJ	\N	\N	\N	\N	\N	t	2	57	2026-01-08 16:41:53.339414	2026-01-08 16:41:53.339416
98	\N	Rancho CPA dos Afonsos	Av. Mal. Fontenelle, 1000 - Campo dos Afonsos	Rio de Janeiro	RJ	\N	\N	\N	\N	\N	t	2	57	2026-01-08 16:41:53.339417	2026-01-08 16:41:53.339418
99	\N	Rancho HAAF	Av. Marechal Fontenelle, n°1000 - Campo dos Afonsos	Rio de Janeiro	RJ	\N	\N	\N	\N	\N	t	2	57	2026-01-08 16:41:53.339419	2026-01-08 16:41:53.33942
100	\N	Rancho UNIFA	Av. Marechal Fontenelle, 1000 - Campo dos Afonsos	Rio de Janeiro	RJ	\N	\N	\N	\N	\N	t	2	57	2026-01-08 16:41:53.339421	2026-01-08 16:41:53.339421
101	\N	Rancho GAP-GL	Estrada do Galeão, S/N - Galeão	Rio de Janeiro	RJ	\N	\N	\N	\N	\N	t	2	58	2026-01-08 16:41:53.34397	2026-01-08 16:41:53.343974
102	\N	Rancho CGABEG	Rua Major Aviador Carlos Biavati S/Nº - Praça do Avião	Rio de Janeiro	RJ	\N	\N	\N	\N	\N	t	2	58	2026-01-08 16:41:53.343976	2026-01-08 16:41:53.343977
103	\N	Rancho HFAG	Estrada do Galeão 4101 - Ilha do Governador	Rio de Janeiro	RJ	\N	\N	\N	\N	\N	t	2	58	2026-01-08 16:41:53.343979	2026-01-08 16:41:53.34398
104	\N	Rancho CEMAL	Estrada do Galeão, 3737 - Galeão	Rio de Janeiro	RJ	\N	\N	\N	\N	\N	t	2	58	2026-01-08 16:41:53.343981	2026-01-08 16:41:53.343982
105	\N	Rancho PAMB	Estrada do Galeão, 4.700 - Ilha do Governador	Rio de Janeiro	RJ	\N	\N	\N	\N	\N	t	2	58	2026-01-08 16:41:53.343984	2026-01-08 16:41:53.343985
106	\N	Rancho BASP	Av. Monteiro Lobato, 6335 - Guarulhos	Guarulhos	SP	\N	\N	\N	\N	\N	t	2	59	2026-01-08 16:41:53.347041	2026-01-08 16:41:53.347045
107	\N	Rancho PAMA-SP	Avenida Braz Leme, 3258 - Santana	São Paulo	SP	\N	\N	\N	\N	\N	t	2	59	2026-01-08 16:41:53.347047	2026-01-08 16:41:53.347048
108	\N	Rancho GAP-SP	Av. Olavo Fontoura, 1300 - Santana	São Paulo	SP	\N	\N	\N	\N	\N	t	2	59	2026-01-08 16:41:53.347049	2026-01-08 16:41:53.34705
109	\N	Rancho HFASP	Av. Olavo Fontoura, 1400 - Santana	São Paulo	SP	\N	\N	\N	\N	\N	t	2	59	2026-01-08 16:41:53.347051	2026-01-08 16:41:53.347052
110	\N	Rancho BAST	Av. Presidente Castelo Branco, s/n°	Guarujá	SP	\N	\N	\N	\N	\N	t	2	59	2026-01-08 16:41:53.347053	2026-01-08 16:41:53.347054
111	\N	Rancho COMGAP	Av. Dom Pedro I, 100 - Cambuci	São Paulo	SP	\N	\N	\N	\N	\N	t	2	59	2026-01-08 16:41:53.347055	2026-01-08 16:41:53.347056
112	\N	Rancho IEAV	Trevo Cel. Av. José Alberto Albano do Amarante, 1 - Putim	São José dos Campos	SP	\N	\N	\N	\N	\N	t	2	60	2026-01-08 16:41:53.349833	2026-01-08 16:41:53.349836
113	\N	Rancho GAP-SJ	Praça Marechal do Ar Eduardo Gomes, nº 50	São José dos Campos	SP	\N	\N	\N	\N	\N	t	2	60	2026-01-08 16:41:53.349837	2026-01-08 16:41:53.349838
114	\N	Rancho GAP-LS	Av. Brigadeiro Eduardo Gomes s/nº - Vila Asas	Lagoa Santa	MG	\N	\N	\N	\N	\N	t	2	61	2026-01-08 16:41:53.351591	2026-01-08 16:41:53.351594
115	\N	Rancho Esquadrão de Saúde	Av. Brigadeiro Eduardo Gomes s/nº - Vila Asas	Lagoa Santa	MG	\N	\N	\N	\N	\N	t	2	61	2026-01-08 16:41:53.351595	2026-01-08 16:41:53.351596
116	\N	Rancho BACO	Rua Augusto Severo, nº 1700 - N. Sra. das Graças	Canoas	RS	\N	\N	\N	\N	\N	t	2	62	2026-01-08 16:41:53.353225	2026-01-08 16:41:53.353228
117	\N	Rancho GAP-CO	Av. Guilherme Schell, 3950 - Fátima	Canoas	RS	\N	\N	\N	\N	\N	t	2	62	2026-01-08 16:41:53.353229	2026-01-08 16:41:53.35323
118	\N	Rancho HACO (Vila Ícaro)	Av. A, nº 100 - Vila Ícaro	Canoas	RS	\N	\N	\N	\N	\N	t	2	62	2026-01-08 16:41:53.353231	2026-01-08 16:41:53.353231
119	\N	Rancho BABE	Rod Arthur Bernardes S/N – Val-de-Cans	Belém	PA	\N	\N	\N	\N	\N	t	2	63	2026-01-08 16:41:53.355014	2026-01-08 16:41:53.355016
120	\N	Rancho GAP-BE	Av. Júlio César, s/n° - Souza	Belém	PA	\N	\N	\N	\N	\N	t	2	63	2026-01-08 16:41:53.355017	2026-01-08 16:41:53.355018
121	\N	Rancho HABE	Av. Almirante Barroso 3492 - Souza	Belém	PA	\N	\N	\N	\N	\N	t	2	63	2026-01-08 16:41:53.355019	2026-01-08 16:41:53.35502
122	\N	Rancho COMARA	Av. Pedro Alvares Cabral, 7115	Belém	PA	\N	\N	\N	\N	\N	t	2	63	2026-01-08 16:41:53.355021	2026-01-08 16:41:53.355021
123	\N	Rancho DACO-MN	Rua Guama, 1 - Colônia Oliveira Machado	Manaus	AM	\N	\N	\N	\N	\N	t	2	64	2026-01-08 16:41:53.357129	2026-01-08 16:41:53.357132
124	\N	Rancho GAP-MN (BAMN)	Avenida Rodrigo Otávio, 430 - Crespo	Manaus	AM	\N	\N	\N	\N	\N	t	2	64	2026-01-08 16:41:53.357133	2026-01-08 16:41:53.357133
125	\N	Rancho HAMN	Av. do Contorno, 780 - Crespo	Manaus	AM	\N	\N	\N	\N	\N	t	2	64	2026-01-08 16:41:53.357134	2026-01-08 16:41:53.357135
126	\N	Rancho GAP-RF	Av. Armindo Moura, 500 - Boa Viagem	Recife	PE	\N	\N	\N	\N	\N	t	2	65	2026-01-08 16:41:53.35931	2026-01-08 16:41:53.359313
127	\N	Rancho HARF	Av. Senador Sérgio Guerra, nº 606 - Piedade	Recife	PE	\N	\N	\N	\N	\N	t	2	65	2026-01-08 16:41:53.359315	2026-01-08 16:41:53.359316
128	\N	Rancho BABR	Área Militar do Aeroporto Internacional	Brasília	DF	\N	\N	\N	\N	\N	t	2	66	2026-01-08 16:41:53.361492	2026-01-08 16:41:53.361495
129	\N	Rancho HFAB	Área Militar do Aeroporto - Lago Sul	Brasília	DF	\N	\N	\N	\N	\N	t	2	66	2026-01-08 16:41:53.361497	2026-01-08 16:41:53.361498
130	\N	Rancho GAP-DF (VI COMAR)	SHIS QI 05 - Área Especial 12 - Lago Sul	Brasília	DF	\N	\N	\N	\N	\N	t	2	66	2026-01-08 16:41:53.361499	2026-01-08 16:41:53.3615
131	\N	Rancho GAP-BR	Esplanada dos Ministérios Bloco M - Anexo A/B	Brasília	DF	\N	\N	\N	\N	\N	t	2	66	2026-01-08 16:41:53.361501	2026-01-08 16:41:53.361502
132	\N	Rancho GABAER	Esplanada dos Ministérios Bloco M - 8º Andar	Brasília	DF	\N	\N	\N	\N	\N	t	2	66	2026-01-08 16:41:53.361503	2026-01-08 16:41:53.361504
133	\N	Rancho BACG	Av. Duque de Caxias, 2905 - Santo Antônio	Campo Grande	MS	\N	\N	\N	\N	\N	t	2	67	2026-01-08 16:41:53.363911	2026-01-08 16:41:53.363913
134	\N	Rancho BASC	Rua do Império, S/N° - Santa Cruz	Rio de Janeiro	RJ	\N	\N	\N	\N	\N	t	2	68	2026-01-08 16:41:53.365848	2026-01-08 16:41:53.365851
135	\N	Rancho FAYS	Rodovia Faria Lima, Km 07	Pirassununga	SP	\N	\N	\N	\N	\N	t	2	69	2026-01-08 16:41:53.367547	2026-01-08 16:41:53.367549
136	\N	Rancho AFA	Estrada de Aguaí, s/nº - Jd. Bandeirantes	Pirassununga	SP	\N	\N	\N	\N	\N	t	2	69	2026-01-08 16:41:53.36755	2026-01-08 16:41:53.367551
137	\N	Rancho EEAR	Av. Brig. Adhemar Lyrio, s/nº	Guaratinguetá	SP	\N	\N	\N	\N	\N	t	2	70	2026-01-08 16:41:53.369662	2026-01-08 16:41:53.369665
138	\N	Rancho EPCAR	Rua Santos Dumont, nº 149	Barbacena	MG	\N	\N	\N	\N	\N	t	2	71	2026-01-08 16:41:53.372142	2026-01-08 16:41:53.372146
139	\N	Rancho CIAAR	Av. Santa Rosa nº 10 - Pampulha	Belo Horizonte	MG	\N	\N	\N	\N	\N	t	2	72	2026-01-08 16:41:53.374423	2026-01-08 16:41:53.374426
140	\N	Rancho BASM	Rodovia RSC 287, Km 240	Santa Maria	RS	\N	\N	\N	\N	\N	t	2	73	2026-01-08 16:41:53.375916	2026-01-08 16:41:53.37592
141	\N	Rancho BAFL	Av. Santos-Dumont, s/n° - Tapera	Florianópolis	SC	\N	\N	\N	\N	\N	t	2	74	2026-01-08 16:41:53.378852	2026-01-08 16:41:53.378856
142	\N	Rancho CINDACTA II	Av. Pref. Erasto Gaertner, 1000 - Bacacheri	Curitiba	PR	\N	\N	\N	\N	\N	t	2	75	2026-01-08 16:41:53.380665	2026-01-08 16:41:53.380668
143	\N	Rancho BABV	Rua Valdemar Bastos de Oliveira, 2990	Boa Vista	RR	\N	\N	\N	\N	\N	t	2	76	2026-01-08 16:41:53.382582	2026-01-08 16:41:53.382584
144	\N	Rancho BAPV	Avenida Lauro Sodré, s/n - Aeroporto	Porto Velho	RO	\N	\N	\N	\N	\N	t	2	77	2026-01-08 16:41:53.383582	2026-01-08 16:41:53.383584
145	\N	Rancho CLA	Rod. MA-106 - Km 7	Alcântara	MA	\N	\N	\N	\N	\N	t	2	78	2026-01-08 16:41:53.384745	2026-01-08 16:41:53.384747
146	\N	Rancho BAFZ	Av Borges de Melo, 205	Fortaleza	CE	\N	\N	\N	\N	\N	t	2	79	2026-01-08 16:41:53.385893	2026-01-08 16:41:53.385896
147	\N	Rancho BANT	Estrada da BANT s/n° - Emaús	Parnamirim	RN	\N	\N	\N	\N	\N	t	2	80	2026-01-08 16:41:53.387095	2026-01-08 16:41:53.387099
148	\N	Rancho CLBI	Rodovia RN 063 - Km 11	Parnamirim	RN	\N	\N	\N	\N	\N	t	2	81	2026-01-08 16:41:53.388299	2026-01-08 16:41:53.388301
149	\N	Rancho CINDACTA III	Av. Maria Irene, s/n° - Jordão	Recife	PE	\N	\N	\N	\N	\N	t	2	82	2026-01-08 16:41:53.389697	2026-01-08 16:41:53.3897
150	\N	Rancho BASV	Av. Tenente Frederico Gustavo dos Santos, s/nº	Salvador	BA	\N	\N	\N	\N	\N	t	2	83	2026-01-08 16:41:53.391263	2026-01-08 16:41:53.391266
151	\N	Rancho CEMCOHA	Av. Oceânica - Ondina	Salvador	BA	\N	\N	\N	\N	\N	t	2	83	2026-01-08 16:41:53.391267	2026-01-08 16:41:53.391269
152	\N	Rancho BAAN	BR 414 KM 4 - Zona Rural	Anápolis	GO	\N	\N	\N	\N	\N	t	2	84	2026-01-08 16:41:53.392434	2026-01-08 16:41:53.392436
\.


--
-- Data for Name: categoria_indicador; Type: TABLE DATA; Schema: public; Owner: qualigestor
--

COPY public.categoria_indicador (id, nome, ordem, cor, ativo, cliente_id) FROM stdin;
\.


--
-- Data for Name: cliente; Type: TABLE DATA; Schema: public; Owner: qualigestor
--

COPY public.cliente (id, nome, razao_social, cnpj, email, telefone, endereco, ativo, criado_em, plano, limite_usuarios, limite_questionarios) FROM stdin;
1	Minha Empresa	Minha Empresa Ltda	\N	contato@empresa.com	\N	\N	t	2025-12-17 15:02:48.488099	basico	10	50
2	Aeronáutica (FAB)	Comando da Aeronáutica	00.394.429/0001-00	sdab@fab.mil.br	None	None	t	2026-01-08 13:25:35.874892	basico	10	50
\.


--
-- Data for Name: configuracao_cliente; Type: TABLE DATA; Schema: public; Owner: qualigestor
--

COPY public.configuracao_cliente (id, logo_url, cor_primaria, cor_secundaria, mostrar_notas, permitir_fotos, obrigar_plano_acao, notificar_aplicacoes_finalizadas, notificar_nao_conformidades, cliente_id, criado_em, atualizado_em) FROM stdin;
1		#007bff	#6c757d	t	t	t	t	t	2	2026-01-18 20:26:42.850049	2026-01-18 20:26:42.850056
\.


--
-- Data for Name: foto_resposta; Type: TABLE DATA; Schema: public; Owner: qualigestor
--

COPY public.foto_resposta (id, caminho, data_upload, resposta_id, tipo) FROM stdin;
3	resposta_335_e971d1ee347f.jpg	2026-01-19 01:23:07.244141	335	evidencia
4	resposta_335_6cb23da3c14b.jpg	2026-01-19 01:23:28.381028	335	evidencia
5	resposta_336_b9622573ed1b.jpg	2026-01-19 01:24:14.290296	336	evidencia
6	resposta_337_9384869f27fb.jpg	2026-01-19 01:24:24.523374	337	evidencia
7	resposta_341_a9ca5d255389.jpg	2026-01-19 01:24:36.992063	341	evidencia
8	resposta_342_00bf7c0449c5.jpg	2026-01-19 01:24:54.977351	342	evidencia
9	resposta_342_3b73b0f5d1ae.jpg	2026-01-19 01:25:12.196474	342	evidencia
10	resposta_345_f1982e0b56b6.jpg	2026-01-19 01:25:28.654305	345	evidencia
11	resposta_346_ffb849837836.jpg	2026-01-19 01:25:40.48045	346	evidencia
12	resposta_351_c46d23099062.jpg	2026-01-19 01:25:57.756724	351	evidencia
13	resposta_352_8a9f99abd1d8.jpg	2026-01-19 01:26:06.179945	352	evidencia
14	resposta_440_d5c774525c16.jpg	2026-01-19 01:37:21.484898	440	evidencia
15	resposta_441_e9e0d1ee3b21.jpg	2026-01-19 01:38:06.595508	441	evidencia
16	resposta_449_cf5b76eef718.jpg	2026-01-19 01:40:48.308992	449	evidencia
17	resposta_420_9aecb26c6c2c.jpg	2026-01-19 01:51:36.919354	420	evidencia
18	resposta_460_41566c73f039.jpg	2026-01-19 01:52:21.316041	460	evidencia
19	resposta_466_91be2f1fbd6c.jpg	2026-01-19 01:52:32.427574	466	evidencia
20	resposta_485_b6e2b102862f.jpg	2026-01-19 01:52:47.867353	485	evidencia
21	resposta_375_c55449b9dac9.jpg	2026-01-19 02:20:03.091158	375	evidencia
22	resposta_447_ba178613094d.jpg	2026-01-19 02:20:28.633895	447	evidencia
23	resposta_452_261396664124.jpg	2026-01-19 02:32:36.674365	452	evidencia
24	resposta_453_fd73742293c8.jpg	2026-01-19 02:32:42.518153	453	evidencia
25	resposta_454_2aa783334208.jpg	2026-01-19 02:32:49.125091	454	evidencia
26	resposta_520_3962fc9d59ae.jpg	2026-01-24 13:22:44.155758	520	evidencia
\.


--
-- Data for Name: grupo; Type: TABLE DATA; Schema: public; Owner: qualigestor
--

COPY public.grupo (id, nome, descricao, cliente_id, ativo, criado_em) FROM stdin;
85	Diretoria de Administração da Aeronáutica - DIRAD		2	t	2026-01-08 17:13:44.458504
86	Teste Dev		2	t	2026-01-17 04:32:31.209057
56	GAP-RJ — Grupamento de Apoio do Rio de Janeiro	\N	2	t	2026-01-08 16:41:53.328148
57	GAP-AF — Grupamento de Apoio dos Afonsos	\N	2	t	2026-01-08 16:41:53.331279
58	GAP-GL — Grupamento de Apoio do Galeão	\N	2	t	2026-01-08 16:41:53.338474
59	GAP-SP — Grupamento de Apoio de São Paulo	\N	2	t	2026-01-08 16:41:53.342683
60	GAP-SJ — Grupamento de Apoio de São José dos Campos	\N	2	t	2026-01-08 16:41:53.346332
61	GAP-LS — Grupamento de Apoio de Lagoa Santa	\N	2	t	2026-01-08 16:41:53.349027
62	GAP-CO — Grupamento de Apoio de Canoas	\N	2	t	2026-01-08 16:41:53.351055
63	GAP-BE — Grupamento de Apoio de Belém	\N	2	t	2026-01-08 16:41:53.352742
64	GAP-MN — Grupamento de Apoio de Manaus	\N	2	t	2026-01-08 16:41:53.35452
65	GAP-RF — Grupamento de Apoio de Recife	\N	2	t	2026-01-08 16:41:53.356553
66	GAP-DF — Grupamento de Apoio do Distrito Federal	\N	2	t	2026-01-08 16:41:53.358558
67	GAP-CG — Grupamento de Apoio de Campo Grande	\N	2	t	2026-01-08 16:41:53.360698
68	BASC — Base Aérea de Santa Cruz	\N	2	t	2026-01-08 16:41:53.362956
69	AFA — Academia da Força Aérea	\N	2	t	2026-01-08 16:41:53.365419
70	EEAR — Escola de Especialistas de Aeronáutica	\N	2	t	2026-01-08 16:41:53.366709
71	EPCAR — Escola Preparatória de Cadetes do Ar	\N	2	t	2026-01-08 16:41:53.368952
72	CIAAR — Centro de Instrução e Adaptação	\N	2	t	2026-01-08 16:41:53.371361
73	BASM — Base Aérea de Santa Maria	\N	2	t	2026-01-08 16:41:53.373772
74	BAFL — Base Aérea de Florianópolis	\N	2	t	2026-01-08 16:41:53.375531
75	CINDACTA II	\N	2	t	2026-01-08 16:41:53.37767
76	BABV — Base Aérea de Boa Vista	\N	2	t	2026-01-08 16:41:53.380114
77	BAPV — Base Aérea de Porto Velho	\N	2	t	2026-01-08 16:41:53.382152
78	CLA — Centro de Lançamento de Alcântara	\N	2	t	2026-01-08 16:41:53.383265
79	BAFZ — Base Aérea de Fortaleza	\N	2	t	2026-01-08 16:41:53.384339
80	BANT — Base Aérea de Natal	\N	2	t	2026-01-08 16:41:53.385517
81	CLBI — Centro de Lançamento da Barreira do Inferno	\N	2	t	2026-01-08 16:41:53.386697
82	CINDACTA III	\N	2	t	2026-01-08 16:41:53.387902
83	BASV — Base Aérea de Salvador	\N	2	t	2026-01-08 16:41:53.389266
84	BAAN — Base Aérea de Anápolis	\N	2	t	2026-01-08 16:41:53.390614
\.


--
-- Data for Name: integracao; Type: TABLE DATA; Schema: public; Owner: qualigestor
--

COPY public.integracao (id, nome, descricao, tipo, configuracao, ativa, criado_em) FROM stdin;
\.


--
-- Data for Name: log_auditoria; Type: TABLE DATA; Schema: public; Owner: qualigestor
--

COPY public.log_auditoria (id, acao, detalhes, entidade_tipo, entidade_id, ip, user_agent, usuario_id, cliente_id, data_acao) FROM stdin;
1	Criou questionário: teste	\N	Questionario	1		Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	1	1	2025-12-17 15:06:52.734227
2	Criou tópico: teste	\N	Topico	1		Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	1	1	2025-12-17 15:07:00.757009
3	Criou pergunta: teste 1...	\N	Pergunta	1		Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	1	1	2025-12-17 15:07:07.214643
4	Criou pergunta: teste 2...	\N	Pergunta	2		Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	1	1	2025-12-17 15:07:15.789586
5	Publicou questionário: teste	\N	Questionario	1		Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	1	1	2025-12-17 15:07:20.654492
6	Criou avaliado	{"nome":"ABC","codigo":""}	Avaliado	1		Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	1	1	2025-12-17 15:07:36.326382
7	Iniciou aplicação do questionário: teste	\N	AplicacaoQuestionario	1		Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	1	1	2025-12-17 15:07:43.477893
8	Finalizou: teste	{"nota":null,"app_id":1}	AplicacaoQuestionario	1		Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	1	1	2025-12-17 15:07:53.016684
9	Criou usuário: Jéssica	\N	Usuario	2		Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	1	1	2025-12-18 16:05:26.21712
10	Criou usuário: José Victor	\N	Usuario	3	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	1	1	2025-12-19 13:20:43.837578
11	Criou questionário: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	Questionario	2	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:20:29.823634
12	Criou tópico: Abertura	\N	Topico	2	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:20:45.041611
13	Criou tópico: Infraestrutura	\N	Topico	3	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:20:51.041504
14	Criou tópico: Higiene e Segurança Pessoal	\N	Topico	4	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:20:57.044707
15	Criou tópico: Higiene e Segurança dos Alimentos	\N	Topico	5	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:21:04.374075
16	Criou tópico: Higiene Ambiental	\N	Topico	6	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:21:08.784136
17	Criou tópico: Armazenagem - Estoque Seco	\N	Topico	7	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:21:16.038451
18	Criou tópico: Armazenagem - Estoque frio	\N	Topico	8	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:21:21.543678
19	Criou tópico: Utensílios, Equipamentos e Mobiliário	\N	Topico	9	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:21:32.819896
20	Criou tópico: Refeição transportada	\N	Topico	10	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:21:37.870792
21	Criou tópico: Lixo e Área de Descarte	\N	Topico	11	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:21:44.753787
22	Criou tópico: Controle de Pragas e Vetores	\N	Topico	12	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:21:49.502961
23	Criou tópico: Registros	\N	Topico	13	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:21:55.226001
24	Criou tópico: Análises Microbiológicas	\N	Topico	14	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:22:03.41561
25	Criou tópico: Vestiários	\N	Topico	15	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:22:05.748424
26	Criou tópico: Qualidade dos cardápios de acordo com a ICA 145-16	\N	Topico	16	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:22:11.501345
27	Criou tópico: Conclusão	\N	Topico	17	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:22:15.428963
28	Criou tópico: Assinaturas	\N	Topico	18	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:22:20.583873
29	Criou pergunta: 1º ou 2º Visita?...	\N	Pergunta	3	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:23:41.380546
30	Criou pergunta: Portas encontram-se em bom estado de conservação (...	\N	Pergunta	4	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:24:14.453195
31	Criou pergunta: Teto, forro e paredes de cor clara, de fácil limpe...	\N	Pergunta	5	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:24:27.640287
32	Criou pergunta: As áreas previstas para manipulação dos alimentos,...	\N	Pergunta	6	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:24:34.481374
33	Criou pergunta: Ventilação adequada em todas as áreas, garantindo ...	\N	Pergunta	7	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:24:43.101769
34	Criou pergunta: Equipamentos de climatização em bom estado de cons...	\N	Pergunta	8	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:24:49.899307
35	Criou pergunta: Presença de sistema de exaustão e/ou insuflamento ...	\N	Pergunta	9	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:24:58.349845
36	Criou pergunta: Janelas, portas e aberturas, incluindo sistema de ...	\N	Pergunta	10	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:25:04.6219
37	Criou pergunta: Piso de material liso, cor clara, de fácil limpeza...	\N	Pergunta	11	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:25:11.63309
38	Criou pergunta: Montacarga e estruturas auxiliares em adequado est...	\N	Pergunta	12	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:25:19.284294
39	Criou pergunta: Possui pias exclusivas para lavagem das mãos na ár...	\N	Pergunta	13	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:25:24.824375
40	Criou pergunta: Caixas de gordura apresentam-se instaladas fora da...	\N	Pergunta	14	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:25:32.812739
41	Criou pergunta: Ralos e grelhas apresentam tampas com dispositivo ...	\N	Pergunta	15	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:25:37.743881
42	Criou pergunta: Iluminação adequada para a atividade desenvolvida,...	\N	Pergunta	16	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:25:45.088885
43	Criou pergunta: Tomadas são identificadas conforme previsto na NR ...	\N	Pergunta	17	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:25:51.286913
44	Criou pergunta: Instalações elétricas encontram-se em bom estado d...	\N	Pergunta	18	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:25:56.990041
45	Criou pergunta: Os extintores estão lacrados, dentro da validade e...	\N	Pergunta	19	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:26:04.987549
46	Criou pergunta: Possui identificação das saídas de emergência?...	\N	Pergunta	20	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:26:11.417512
47	Criou pergunta: Há  local  apropriado  para  a  estocagem  de  mat...	\N	Pergunta	21	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:26:18.998247
48	Criou pergunta: Descrever aqui, com maiores detalhes, os óbices en...	\N	Pergunta	22	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:26:57.248891
49	Criou pergunta: Os uniformes são adequados para área de manipulaçã...	\N	Pergunta	23	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:27:34.1353
50	Criou pergunta: Utilizam corretamente a proteção para os cabelos (...	\N	Pergunta	24	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:29:17.41252
51	Criou pergunta: Possuem hábitos adequados de higiene pessoal (unha...	\N	Pergunta	25	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:29:22.461038
52	Criou pergunta: Quando o funcionário possui corte ou ferida é util...	\N	Pergunta	26	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:29:31.017322
53	Criou pergunta: O controle da saúde dos manipuladores ocorre anual...	\N	Pergunta	27	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:29:41.306628
54	Criou pergunta: Possuem EPI em estoque e o material está disponíve...	\N	Pergunta	28	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:29:49.092189
55	Criou pergunta: Fazem uso correto  de EPIs ( óculos, avental, luva...	\N	Pergunta	29	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:29:55.863506
56	Criou pergunta: Presença de material para a higiene das mãos (sabã...	\N	Pergunta	30	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:30:04.647382
57	Criou pergunta: Ausência de utilização de celular, fone de ouvido ...	\N	Pergunta	31	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:30:14.785089
58	Criou pergunta: Roupas e objetos pessoais guardados em local espec...	\N	Pergunta	32	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:30:19.871432
59	Criou pergunta: Existem cartazes de orientação aos manipuladores s...	\N	Pergunta	33	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:30:28.26664
60	Criou pergunta: Funcionários responsáveis pela atividade de higien...	\N	Pergunta	34	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:32:41.2319
61	Criou pergunta: Descrever aqui, com maiores detalhes, os óbices en...	\N	Pergunta	35	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:32:54.44292
62	Criou pergunta: Procedimento de higienização dos hortifrutis é rea...	\N	Pergunta	36	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:34:19.032368
63	Criou pergunta: Placas de corte estão limpas?...	\N	Pergunta	37	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:34:24.037668
64	Criou pergunta: Procedimento de descongelamento é realizado corret...	\N	Pergunta	38	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:34:31.927272
65	Criou pergunta: Fluxos e procedimentos seguros, eliminando os risc...	\N	Pergunta	39	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:34:38.17627
66	Criou pergunta: O arroz e feijão são lavados a cada utilização?...	\N	Pergunta	40	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:34:51.468223
67	Criou pergunta: As preparações prontas estão cobertas, tampadas e ...	\N	Pergunta	41	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:34:57.067825
68	Criou pergunta: Temperatura de manutenção adequada dos alimentos p...	\N	Pergunta	42	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:35:02.81299
69	Criou pergunta: Temperatura de manutenção adequada dos alimentos p...	\N	Pergunta	43	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:35:22.809823
70	Criou pergunta: São armazenadas amostras de contra prova de alimen...	\N	Pergunta	44	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:35:28.204496
71	Criou pergunta: Existência de reservatório de água acessível dotad...	\N	Pergunta	45	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:35:34.625351
72	Criou pergunta: Gelo usado em contato direto com alimentos e bebid...	\N	Pergunta	46	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:35:39.812746
73	Criou pergunta: Existem filtros de água? Os filtros são limpos reg...	\N	Pergunta	47	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:35:45.338452
74	Criou pergunta: O reaproveitamento de sobras limpas é adequado?...	\N	Pergunta	48	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:35:52.140916
75	Criou pergunta: Visitantes cumprem os requisitos de higiene e saúd...	\N	Pergunta	49	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:36:00.679394
76	Criou pergunta: Descrever aqui, com maiores detalhes, os óbices en...	\N	Pergunta	50	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:36:05.609436
77	Editou pergunta: Descrever aqui, com maiores detalhes, os óbices en...	\N	Pergunta	50	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:36:14.582221
78	Criou pergunta: Estão presentes todos os materiais de limpeza (det...	\N	Pergunta	51	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:37:34.413814
79	Criou pergunta: Superfície de manipulação, preparo e distribuição ...	\N	Pergunta	52	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:37:42.099136
80	Criou pergunta: Esponjas/ Fibras estão em boas condições de uso?...	\N	Pergunta	53	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:37:47.775004
81	Criou pergunta: Ausência de esponja imersa em solução detergente?...	\N	Pergunta	54	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:37:56.378036
82	Criou pergunta: Fazem uso de pano descartável?...	\N	Pergunta	55	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:38:04.08158
83	Criou pergunta: MOP/esfregão/pano de chão estão limpos?...	\N	Pergunta	56	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:38:17.439649
84	Criou pergunta: Os tetos, portas, paredes, pisos, janelas e telas ...	\N	Pergunta	57	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:38:22.631701
85	Criou pergunta: O acesso a cozinha garante a proteção contra a ent...	\N	Pergunta	58	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:38:27.385236
86	Criou pergunta: Produtos de limpeza (detergentes e desinfetantes) ...	\N	Pergunta	59	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:38:32.291663
87	Criou pergunta: Refeitório limpo e organizado?...	\N	Pergunta	60	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:38:36.697918
88	Criou pergunta: Utensílios utilizados na higienização de instalaçõ...	\N	Pergunta	61	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:38:41.267415
89	Criou pergunta: Descrever aqui, com maiores detalhes, os óbices en...	\N	Pergunta	62	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:39:04.010583
90	Criou pergunta: Os pisos, paredes e prateleiras encontram-se limpo...	\N	Pergunta	63	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:41:45.084291
91	Criou pergunta: As caixas plásticas estão limpas?...	\N	Pergunta	64	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:41:51.509127
92	Criou pergunta: A armazenagem segue o PVPS (primeiro que vence, pr...	\N	Pergunta	65	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:41:57.747547
93	Criou pergunta: Os produtos estão dentro do prazo de validade?...	\N	Pergunta	66	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:42:04.47898
94	Criou pergunta: Os produtos encontram-se com rotulagem completa?...	\N	Pergunta	67	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:42:10.345031
95	Criou pergunta: Produtos e embalagens mantidos devidamente fechado...	\N	Pergunta	68	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:42:15.167311
96	Criou pergunta: Produtos armazenados sob estrados e/ou prateleiras...	\N	Pergunta	69	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:42:19.909774
97	Criou pergunta: Cantos e paredes desobstruídos, sem produtos encos...	\N	Pergunta	70	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:42:26.215307
98	Criou pergunta: As caixas plásticas e monoblocos foram higienizado...	\N	Pergunta	71	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:43:00.662606
99	Criou pergunta: Os produtos recebidos foram retirados das embalage...	\N	Pergunta	72	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:43:07.432118
100	Criou pergunta: Os alimentos encontram-se armazenados separados do...	\N	Pergunta	73	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:43:12.309597
101	Criou pergunta: Descrever aqui, com maiores detalhes, os óbices en...	\N	Pergunta	74	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:43:24.81046
102	Editou pergunta: Descrever aqui, com maiores detalhes, os óbices en...	\N	Pergunta	62	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:43:39.33568
103	Criou pergunta: Os pisos, paredes e prateleiras encontram-se limpo...	\N	Pergunta	75	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:45:53.512127
104	Criou pergunta: Caixas plásticas foram higienizados antes da utili...	\N	Pergunta	76	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:45:58.540757
105	Criou pergunta: Os produtos recebidos foram retirados das embalage...	\N	Pergunta	77	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:46:03.762849
106	Criou pergunta: Na câmara, os produtos em preparação, os produtos ...	\N	Pergunta	78	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:46:08.555334
107	Criou pergunta: Na presença de caixas de papelão, as mesmas encont...	\N	Pergunta	79	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:46:13.344021
108	Criou pergunta: Produtos e embalagens mantidos devidamente fechado...	\N	Pergunta	80	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:46:17.54732
109	Criou pergunta: Preparações e sobras estão identificadas (nome e v...	\N	Pergunta	81	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:46:22.001594
110	Criou pergunta: Ausência de ralos no interior das câmaras frigoríf...	\N	Pergunta	82	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:46:27.4677
111	Criou pergunta: Ausência de alimentos deteriorados nas geladeiras ...	\N	Pergunta	83	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:46:32.388996
112	Criou pergunta: Câmara de congelamento em funcionamento adequado (...	\N	Pergunta	84	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:46:36.93205
113	Criou pergunta: Câmara de resfriamento em funcionamento adequado (...	\N	Pergunta	85	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:46:42.028011
114	Criou pergunta: O sistema de refrigeração está livre de sujidades?...	\N	Pergunta	86	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:46:49.091005
115	Criou pergunta: Descrever aqui, com maiores detalhes, os óbices\r\n ...	\N	Pergunta	87	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:46:57.461744
116	Criou pergunta: Os equipamentos da linha de produção estão em núme...	\N	Pergunta	88	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:47:47.664767
117	Editou pergunta: Descrever aqui, com maiores detalhes, os óbices\r\n ...	\N	Pergunta	87	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:47:57.370027
118	Criou pergunta: Os equipamentos que necessitam de limpeza orgânica...	\N	Pergunta	89	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:48:07.089995
119	Criou pergunta: Os demais equipamentos  da cozinha são de material...	\N	Pergunta	90	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:48:12.333565
120	Criou pergunta: Os utensílios estão limpos, de material adequado e...	\N	Pergunta	91	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:48:17.652991
121	Criou pergunta: Equipamentos e utensílios guardados corretamente?...	\N	Pergunta	92	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:48:22.573101
122	Criou pergunta: Máquinas de lavar com utilização de água quente?...	\N	Pergunta	93	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:48:27.862951
123	Criou pergunta: Máquinas de lavar (cortinas, reservatório etc.) em...	\N	Pergunta	94	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:48:32.635887
124	Criou pergunta: Presença de detergente e secante devidamente insta...	\N	Pergunta	95	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:48:37.345527
125	Criou pergunta: Ausência de equipamentos fora de uso ou quebrado?...	\N	Pergunta	96	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:48:41.798409
126	Criou pergunta: Mobiliário em número suficiente, de material aprop...	\N	Pergunta	97	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:48:47.735912
127	Criou pergunta: Descrever aqui, com maiores detalhes, os óbices en...	\N	Pergunta	98	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:48:56.263902
128	Criou pergunta: As preparações transportadas estão acondicionadas ...	\N	Pergunta	99	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:49:15.467572
129	Criou pergunta: As preparações sofrem reaquecimento assim que cheg...	\N	Pergunta	100	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:49:21.07638
130	Criou pergunta: As preparações estão na temperatura adequada no mo...	\N	Pergunta	101	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:49:25.676414
131	Criou pergunta: Os veículos de transporte são utilizados apenas pa...	\N	Pergunta	102	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:49:30.00435
132	Criou pergunta: Os veículos de transporte estão higienizados?...	\N	Pergunta	103	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:49:34.466364
133	Criou pergunta: Descrever aqui, com maiores detalhes, os óbices en...	\N	Pergunta	104	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:49:45.588486
134	Criou pergunta: O lixo se encontra em área limpa, organizada e iso...	\N	Pergunta	105	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:50:06.677943
135	Criou pergunta: Ausência de lixo na área externa?...	\N	Pergunta	106	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:50:11.613832
136	Criou pergunta: As lixeiras internas estão tampadas,  limpas, forr...	\N	Pergunta	107	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:50:16.339236
137	Criou pergunta: As lixeiras internas possuem tampa e acionamento p...	\N	Pergunta	108	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:50:22.456803
138	Criou pergunta: Resíduo orgânico armazenado em área refrigerada?...	\N	Pergunta	109	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:50:27.017794
139	Criou pergunta: Presença de coleta seletiva?...	\N	Pergunta	110	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:50:31.525406
140	Criou pergunta: Descrever aqui, com maiores detalhes, os óbices en...	\N	Pergunta	111	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:50:40.630771
141	Criou pergunta: Ausência de pragas e vetores ou os seus vestígios?...	\N	Pergunta	112	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:50:56.568061
142	Criou pergunta: Ausência de telas rasgadas, ralos abertos e lixo e...	\N	Pergunta	113	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:51:02.867285
143	Criou pergunta: Presença de registro em dia de aplicação do serviç...	\N	Pergunta	114	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:51:08.63878
144	Criou pergunta: Descrever aqui, com maiores detalhes, os óbices en...	\N	Pergunta	115	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:51:15.686265
145	Criou pergunta: Possui manual de boas práticas de fabricação atual...	\N	Pergunta	116	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:51:34.011559
146	Criou pergunta: A unidade possui termômetro para realizar os regis...	\N	Pergunta	117	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:51:43.843854
147	Criou pergunta: São realizados registros de monitoramento de tempe...	\N	Pergunta	118	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:51:49.031333
148	Criou pergunta: São realizados registros de monitoramento de higie...	\N	Pergunta	119	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:51:53.257173
149	Criou pergunta: São realizados registros de monitoramento de higie...	\N	Pergunta	120	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:51:58.149781
150	Criou pergunta: São realizados registros diários do acompanhamento...	\N	Pergunta	121	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:52:02.928005
151	Criou pergunta: Existência de registro da execução de higienização...	\N	Pergunta	122	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:52:08.051274
152	Criou pergunta: Existência de registros de manutenção preventiva d...	\N	Pergunta	123	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:52:13.22615
153	Criou pergunta: Existência de registros de manutenção corretiva do...	\N	Pergunta	124	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:52:22.53162
154	Criou pergunta: Existência de registros de manutenção, operação e ...	\N	Pergunta	125	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:52:27.910428
155	Criou pergunta: Existência de registros de calibração dos termômet...	\N	Pergunta	126	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:52:32.274245
156	Criou pergunta: Existência de registros de calibração das balanças...	\N	Pergunta	127	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:52:37.584378
157	Criou pergunta: Existência do quadro de avisos fixado em área de g...	\N	Pergunta	128	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:52:43.018364
158	Criou pergunta: Existência de registro de limpeza das caixas de go...	\N	Pergunta	129	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:52:47.715629
159	Criou pergunta: Existência de registro das análises de potabilidad...	\N	Pergunta	130	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:52:53.60884
160	Criou pergunta: Existência de registro da validade e substituição ...	\N	Pergunta	131	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:52:57.957266
161	Criou pergunta: Existência de registro dos caso suspeitos de Doenç...	\N	Pergunta	132	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:53:02.45296
162	Criou pergunta: Descrever aqui, com maiores detalhes, os óbices en...	\N	Pergunta	133	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:53:10.313755
163	Criou pergunta: Os laudos dos alimentos apresentaram resultados sa...	\N	Pergunta	134	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:53:54.003589
164	Criou pergunta: Os laudos dos swabs de manipuladores apresentaram ...	\N	Pergunta	135	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:53:58.782927
165	Criou pergunta: Os laudos dos swabs de equipamentos apresentaram r...	\N	Pergunta	136	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:54:04.064867
166	Criou pergunta: Os laudos dos swabs de utensílios apresentaram res...	\N	Pergunta	137	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:54:09.62083
167	Criou pergunta: Os laudos dos swabs de superfície apresentaram res...	\N	Pergunta	138	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:54:15.262525
168	Criou pergunta: O laudo da água apresentou resultado satisfatório?...	\N	Pergunta	139	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:54:20.408902
169	Criou pergunta: Descrever aqui quais amostras apresentaram resulta...	\N	Pergunta	140	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:54:25.049393
170	Editou pergunta: Descrever aqui quais amostras apresentaram resulta...	\N	Pergunta	140	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:54:33.192937
171	Criou pergunta: Vestiários e sanitários respeitam as exigências de...	\N	Pergunta	141	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:55:42.044858
172	Criou pergunta: Vestiários e sanitários são servidos de água corre...	\N	Pergunta	142	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:55:46.341015
173	Criou pergunta: Vasos sanitários e chuveiros em número suficiente?...	\N	Pergunta	143	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:55:50.750775
174	Criou pergunta: Instalações sanitárias dotadas de lavatórios e de ...	\N	Pergunta	144	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:55:56.855116
175	Criou pergunta: Vestiários dotados de armários em número suficient...	\N	Pergunta	145	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:56:01.939358
176	Criou pergunta: Vestiários apresentam bom estado de conservação?...	\N	Pergunta	146	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:56:07.654294
177	Criou pergunta: Descrever aqui, com maiores detalhes, os óbices en...	\N	Pergunta	147	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:56:16.364383
178	Criou pergunta: Possui cardápio semanal exposto em local visível e...	\N	Pergunta	148	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:56:37.534682
179	Criou pergunta: Existem Fichas técnicas  para as preparações previ...	\N	Pergunta	149	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:56:42.993925
180	Criou pergunta: Os cardápios semanais são disponibilizados antecip...	\N	Pergunta	150	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:56:47.834905
181	Criou pergunta: Para os casos de dietas especiais, direcionada aos...	\N	Pergunta	151	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:56:52.720659
182	Criou pergunta: É realizado promoção da saúde e prevenção de doenç...	\N	Pergunta	152	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:56:57.673499
183	Criou pergunta: O resultado do indicador de qualidade dos cardápio...	\N	Pergunta	153	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:57:02.852463
184	Criou pergunta: Descrever aqui, com maiores detalhes, os óbices en...	\N	Pergunta	154	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:57:07.764734
185	Editou pergunta: Descrever aqui, com maiores detalhes, os óbices en...	\N	Pergunta	154	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:57:19.850421
186	Criou pergunta: TREINAMENTO -  Descrever a temática abordada, meto...	\N	Pergunta	155	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:57:41.344148
187	Removeu pergunta: TREINAMENTO -  Descrever a temática abordada, meto...	\N	Pergunta	155	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:57:53.127827
188	Criou pergunta: TREINAMENTO -  Descrever a temática abordada, meto...	\N	Pergunta	156	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:58:05.33706
189	Criou pergunta: OBSERVAÇÕES GERAIS E DIFICULDADES ENCONTRADAS PARA...	\N	Pergunta	157	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:58:11.572674
190	Criou pergunta: Nome do Militar Responsável pela visita...	\N	Pergunta	158	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:58:36.850374
191	Criou pergunta: Assinatura do Militar Responsável pela visita...	\N	Pergunta	159	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 15:58:48.160874
192	Criou pergunta: Nome do consultor Responsável pela visita...	\N	Pergunta	160	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 16:00:21.733054
193	Editou pergunta: Nome do consultor Responsável pela visita...	\N	Pergunta	160	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 16:00:26.649883
194	Criou pergunta: Assinatura do consultor Responsável pela visita...	\N	Pergunta	161	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 16:00:36.519143
195	Publicou questionário: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	Questionario	2	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 16:00:45.785426
196	Desativou questionário: teste	\N	Questionario	1	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 17:23:07.57295
197	Criou avaliado	{"nome":"GAP-SJ","codigo":""}	Avaliado	2	127.0.0.1	Mozilla/5.0 (iPhone; CPU iPhone OS 18_7_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/143.0.7499.151 Mobile/15E148 Safari/604.1	3	1	2026-01-02 20:45:14.007523
198	Iniciou aplicação do questionário: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	AplicacaoQuestionario	2	127.0.0.1	Mozilla/5.0 (iPhone; CPU iPhone OS 18_7_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/143.0.7499.151 Mobile/15E148 Safari/604.1	3	1	2026-01-02 20:45:31.987901
199	Finalizou: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	{"nota":95.45,"app_id":2}	AplicacaoQuestionario	2	127.0.0.1	Mozilla/5.0 (iPhone; CPU iPhone OS 18_7_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/143.0.7499.151 Mobile/15E148 Safari/604.1	3	1	2026-01-02 21:11:55.094986
200	Editou pergunta: Descrever aqui, com maiores detalhes, os óbices en...	\N	Pergunta	50	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 21:48:56.306018
201	Reabriu aplicação: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	AplicacaoQuestionario	2	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 21:49:23.210902
202	Finalizou: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	{"nota":96.18,"app_id":2}	AplicacaoQuestionario	2	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-02 21:49:46.606083
203	Reabriu aplicação: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	AplicacaoQuestionario	2	127.0.0.1	Mozilla/5.0 (iPhone; CPU iPhone OS 18_7_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/143.0.7499.151 Mobile/15E148 Safari/604.1	3	1	2026-01-04 20:22:41.033754
204	Iniciou aplicação do questionário: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	AplicacaoQuestionario	3	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	1	2026-01-06 17:43:40.69743
205	Criou pergunta: Ausência de caixas de papelão e/ou materiais não a...	\N	Pergunta	162	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	1	2026-01-07 16:34:39.944857
206	Reordenou perguntas do tópico: Armazenagem - Estoque frio	\N	Topico	8	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 13:52:38.055091
207	Reordenou perguntas do tópico: Armazenagem - Estoque frio	\N	Topico	8	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 13:52:42.074666
208	Reordenou perguntas do tópico: Armazenagem - Estoque frio	\N	Topico	8	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 13:52:44.875887
209	Criou pergunta: Possui o certificado de coleta e transporte de óle...	\N	Pergunta	163	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 13:55:23.901018
210	Reordenou perguntas do tópico: Lixo e Área de Descarte	\N	Topico	11	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 13:55:36.601886
211	Reordenou perguntas do tópico: Lixo e Área de Descarte	\N	Topico	11	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 13:55:57.016908
212	Criou pergunta: Presença de Manifesto de Transporte de Resíduos e ...	\N	Pergunta	164	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 13:56:37.04391
213	Reordenou perguntas do tópico: Lixo e Área de Descarte	\N	Topico	11	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 13:56:43.455453
214	Criou tópico: Efetivo do Rancho	\N	Topico	19	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 13:59:11.373617
215	Criou pergunta: A OM possui militar técnico em Nutrição?...	\N	Pergunta	165	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 13:59:40.148045
216	Criou pergunta: Caso sim, realiza a elaboração/atualização de fich...	\N	Pergunta	166	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 14:02:17.195894
217	Reordenou tópicos do questionário: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	Questionario	2	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 14:03:14.158813
218	Criou tópico: Ambiente e conforto - Refeitórios	\N	Topico	20	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 14:03:42.451286
219	Reordenou tópicos do questionário: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	Questionario	2	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 14:03:48.22265
220	Criou pergunta: O refeitório possui sistema de climatização?...	\N	Pergunta	167	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 14:04:26.298432
221	Criou usuário: José Victor Fernandez (super_admin)	\N	Usuario	4	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	2	2026-01-08 14:31:34.318365
222	Excluiu avaliado	{"id":1,"nome":"ABC"}	Avaliado	1	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	2	2026-01-08 15:23:23.009064
223	Criou pergunta: A temperatura do ambiente é confortável nos horári...	\N	Pergunta	168	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 16:06:13.421667
224	Criou pergunta: As mesas e cadeiras são confortáveis, bem distribu...	\N	Pergunta	169	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 16:06:41.159189
225	Criou pergunta: A iluminação do ambiente é adequada para uma refei...	\N	Pergunta	170	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 16:07:05.072152
226	Criou pergunta: Há talheres, copos e pratos disponíveis em quantid...	\N	Pergunta	171	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 16:07:21.411285
227	Criou pergunta: Os utensílios estão limpos, organizados e em bom e...	\N	Pergunta	172	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 16:07:41.227341
228	Criou pergunta: Os equipamentos de distribuição dos alimentos (bal...	\N	Pergunta	173	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 16:08:08.852329
229	Criou pergunta: Existe reposição eficiente e rápida de utensílios ...	\N	Pergunta	174	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 16:08:23.983454
230	Criou pergunta: O refeitório apresenta , de forma geral, um ambien...	\N	Pergunta	175	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 16:12:47.482899
231	Criou pergunta: A temperatura dos alimentos está adequada, respeit...	\N	Pergunta	176	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 16:13:07.902482
232	Criou pergunta: As preparações apresentam boa aparência (cor, text...	\N	Pergunta	177	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 16:13:33.912538
233	Criou pergunta: O fluxo de atendimento no refeitório é eficiente, ...	\N	Pergunta	178	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	2	2	2026-01-08 16:14:04.646443
234	Excluiu avaliado	{"id":96,"nome":"Rancho DIRAD"}	Avaliado	96	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	2	2026-01-08 17:02:40.419668
235	Criou grupo: Diretoria de Administração da Aeronáutica - DIRAD	\N	Grupo	85	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	2	2026-01-08 17:13:44.469683
236	Criou avaliado	{"nome":"DIRAD","codigo":""}	Avaliado	153	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	2	2026-01-08 17:14:18.255802
237	Criou usuário: Mônica (auditor)	\N	Usuario	5	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	2	2026-01-08 18:10:13.609376
238	Criou usuário: Rejane (auditor)	\N	Usuario	6	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	2	2026-01-08 21:25:44.741954
239	Editou pergunta: Portas encontram-se em bom estado de conservação (...	\N	Pergunta	4	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	6	2	2026-01-08 22:59:40.790867
240	Criou usuário: PAME-RJ (usuario)	\N	Usuario	7	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36	3	2	2026-01-09 00:45:20.644793
241	Criou novo questionário: Teste IA	\N	Questionario	3	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-17 04:28:02.789796
242	Criou tópico: Rotina ao Acordar em cas	\N	Topico	21	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-17 04:28:32.071798
243	Criou pergunta: Levantou no horário correto?...	\N	Pergunta	179	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-17 04:29:02.659702
244	Criou pergunta: Arrumou a cama?...	\N	Pergunta	180	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-17 04:29:20.331672
245	Criou pergunta: Escovou os dentes antes do café?...	\N	Pergunta	181	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-17 04:29:35.711119
246	Publicou questionário: Teste IA	\N	Questionario	3	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-17 04:29:42.441449
247	Criou avaliado	{"nome":"Teste de desenvolvimento","codigo":""}	Avaliado	154	127.0.0.1	Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.7.3 Mobile/15E148 Safari/604.1	3	2	2026-01-17 04:32:03.267107
248	Criou grupo: Teste Dev	\N	Grupo	86	127.0.0.1	Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.7.3 Mobile/15E148 Safari/604.1	3	2	2026-01-17 04:32:31.217159
249	Editou pergunta: Levantou no horário correto?...	\N	Pergunta	179	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-17 04:34:00.464887
250	Editou pergunta: Arrumou a cama?...	\N	Pergunta	180	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-17 04:34:04.617167
251	Editou pergunta: Arrumou a cama?...	\N	Pergunta	180	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-17 04:34:08.796522
252	Editou pergunta: Arrumou a cama?...	\N	Pergunta	180	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-17 04:34:09.095497
253	Editou pergunta: Escovou os dentes antes do café?...	\N	Pergunta	181	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-17 04:34:13.37802
254	Finalizou: Teste IA	{"nota":66.67,"app_id":10}	AplicacaoQuestionario	10	127.0.0.1	Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.7.3 Mobile/15E148 Safari/604.1	3	2	2026-01-17 04:38:25.598057
255	Reabriu aplicação: Teste IA	\N	AplicacaoQuestionario	10	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36 Edg/143.0.0.0	3	2	2026-01-17 21:30:58.852458
256	Reordenou tópicos do questionário: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	Questionario	2	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-18 16:59:47.601716
257	Removeu tópico: Abertura e 1 perguntas	\N	Topico	2	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-18 16:59:57.180302
258	Reordenou tópicos do questionário: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	Questionario	2	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-18 17:00:08.222961
259	Reordenou tópicos do questionário: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	Questionario	2	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-18 17:00:09.805337
260	Editou pergunta: Portas encontram-se em bom estado de conservação (...	\N	Pergunta	4	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-18 17:00:24.805141
261	Editou pergunta: Teto, forro e paredes de cor clara, de fácil limpe...	\N	Pergunta	5	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-18 17:00:31.456002
262	Editou pergunta: As áreas previstas para manipulação dos alimentos,...	\N	Pergunta	6	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-18 17:00:36.912927
263	Editou pergunta: Ventilação adequada em todas as áreas, garantindo ...	\N	Pergunta	7	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-18 17:00:41.164921
264	Editou pergunta: Ventilação adequada em todas as áreas, garantindo ...	\N	Pergunta	7	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-18 17:00:45.747548
265	Editou pergunta: Equipamentos de climatização em bom estado de cons...	\N	Pergunta	8	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-18 17:00:52.774476
266	Editou pergunta: Ventilação adequada em todas as áreas, garantindo ...	\N	Pergunta	7	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-18 17:01:16.82238
267	Editou pergunta: Presença de sistema de exaustão e/ou insuflamento ...	\N	Pergunta	9	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-18 17:01:22.601145
268	Editou pergunta: Janelas, portas e aberturas, incluindo sistema de ...	\N	Pergunta	10	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-18 17:01:26.949827
269	Editou pergunta: Piso de material liso, cor clara, de fácil limpeza...	\N	Pergunta	11	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-18 17:01:34.627518
270	Editou pergunta: Montacarga e estruturas auxiliares em adequado est...	\N	Pergunta	12	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-18 17:01:40.824911
271	Editou pergunta: Possui pias exclusivas para lavagem das mãos na ár...	\N	Pergunta	13	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-18 17:01:45.996543
272	Editou pergunta: Caixas de gordura apresentam-se instaladas fora da...	\N	Pergunta	14	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-18 17:02:39.936757
273	Criou usuário: Teste Gestor (gestor)	\N	Usuario	8	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-19 00:04:33.066498
274	Criou usuário: Teste Rancho (usuario)	\N	Usuario	9	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	3	2	2026-01-19 00:05:17.84312
275	Criou tópico: teste	\N	Topico	22	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	9	2	2026-01-19 00:06:53.013537
276	Criou usuário: Mônica (auditor)	\N	Usuario	10	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-19 00:50:59.367192
277	Editou pergunta: Descrever aqui, com maiores detalhes, os óbices en...	\N	Pergunta	133	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	9	2	2026-01-19 01:38:49.379767
278	Editou pergunta: Descrever aqui, com maiores detalhes, os óbices en...	\N	Pergunta	115	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	9	2	2026-01-19 01:39:52.770755
279	Editou pergunta: TREINAMENTO -  Descrever a temática abordada, meto...	\N	Pergunta	156	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	9	2	2026-01-19 01:47:06.587238
280	Editou pergunta: OBSERVAÇÕES GERAIS E DIFICULDADES ENCONTRADAS PARA...	\N	Pergunta	157	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0	9	2	2026-01-19 01:47:12.61289
281	Finalizou: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	{"nota":88.1,"app_id":15}	AplicacaoQuestionario	15	127.0.0.1	Mozilla/5.0 (iPhone; CPU iPhone OS 18_7_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/144.0.7559.85 Mobile/15E148 Safari/604.1	10	2	2026-01-19 02:33:00.957936
282	Reabriu aplicação: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	AplicacaoQuestionario	15	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-22 10:58:45.616597
283	Finalizou: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	{"nota":88.1,"app_id":15}	AplicacaoQuestionario	15	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-22 10:59:57.342506
284	Reabriu aplicação: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	AplicacaoQuestionario	15	127.0.0.1	Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/17.5 Mobile/15A5370a Safari/602.1	3	2	2026-01-22 13:15:18.002251
285	Finalizou: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	{"nota":88.1,"app_id":15}	AplicacaoQuestionario	15	127.0.0.1	Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/17.5 Mobile/15A5370a Safari/602.1	3	2	2026-01-22 13:15:43.124545
286	Reabriu aplicação: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	AplicacaoQuestionario	15	127.0.0.1	Mozilla/5.0 (iPhone; CPU iPhone OS 18_7_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/144.0.7559.85 Mobile/15E148 Safari/604.1	3	2	2026-01-22 15:06:07.022458
287	Finalizou: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	{"nota":88.1,"app_id":15}	AplicacaoQuestionario	15	127.0.0.1	Mozilla/5.0 (iPhone; CPU iPhone OS 18_7_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/144.0.7559.85 Mobile/15E148 Safari/604.1	3	2	2026-01-22 15:09:55.457833
288	Reabriu aplicação: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	AplicacaoQuestionario	15	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-22 17:45:13.280502
289	Finalizou: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	{"nota":88.1,"app_id":15}	AplicacaoQuestionario	15	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-22 17:46:16.520743
290	Reabriu aplicação: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	AplicacaoQuestionario	15	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-22 18:18:57.155249
291	Finalizou: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	{"nota":88.1,"app_id":15}	AplicacaoQuestionario	15	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-22 18:19:49.652557
292	Reabriu aplicação: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	AplicacaoQuestionario	15	127.0.0.1	Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/17.5 Mobile/15A5370a Safari/602.1	3	2	2026-01-23 17:26:53.268724
293	Finalizou: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	{"nota":88.1,"app_id":15}	AplicacaoQuestionario	15	127.0.0.1	Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/17.5 Mobile/15A5370a Safari/602.1	3	2	2026-01-23 17:29:06.540572
294	Reabriu aplicação: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	AplicacaoQuestionario	15	127.0.0.1	Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/17.5 Mobile/15A5370a Safari/602.1	3	2	2026-01-23 17:29:22.556299
295	Criou usuário: Luiza Marcelle (auditor)	\N	Usuario	11	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:23:56.380632
296	Criou usuário: Dandara Santanna Laut (auditor)	\N	Usuario	12	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:25:37.365741
297	Criou usuário: Ana Claudia  Lourenço Magalhães (auditor)	\N	Usuario	13	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:30:31.730428
298	Criou usuário: Paula Ferreira  Rita da Silva (auditor)	\N	Usuario	14	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:31:13.028456
299	Criou usuário: Fernanda Cristina  Biagiotti de Souza (auditor)	\N	Usuario	15	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:32:22.308442
300	Criou usuário: Elisabete Carrieri (auditor)	\N	Usuario	16	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:32:45.055446
301	Criou usuário: Maria Cristina  Almeida Pinto (auditor)	\N	Usuario	17	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:33:18.061431
302	Criou usuário: Monica Queiroz Lobo (auditor)	\N	Usuario	18	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:34:56.460632
309	Criou usuário: Andrea Flores Oliveira (auditor)	\N	Usuario	25	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:41:07.410956
314	Criou usuário: Augiceli Barbosa  De Oliveira Rodrigues (auditor)	\N	Usuario	30	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:43:31.681296
319	Criou usuário: Iasmine Vasconcelos  Villa (auditor)	\N	Usuario	35	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:45:43.713636
303	Criou usuário: Mariana Ferreira da Silva (auditor)	\N	Usuario	19	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:35:22.752602
310	Criou usuário: Pâmela Esmeralda (auditor)	\N	Usuario	26	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:41:29.344279
315	Criou usuário: Rebeka (auditor)	\N	Usuario	31	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:44:14.630169
320	Criou usuário: Débora Lovisi  Silva Gomide (auditor)	\N	Usuario	36	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:46:59.456468
304	Criou usuário: Deisiane Franciele  da Silva Costa (auditor)	\N	Usuario	20	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:36:03.385732
311	Criou usuário: Karla Andréa Costa Cunto (auditor)	\N	Usuario	27	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:42:00.9769
316	Criou usuário: "Alcione Maria  Moreira de Oliveira " (auditor)	\N	Usuario	32	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:44:32.251537
321	Criou usuário: Samara Cristina  Pereira curado (auditor)	\N	Usuario	37	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:47:30.501597
305	Criou usuário: Mirlene Sena Costa (auditor)	\N	Usuario	21	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:37:41.661758
307	Criou usuário: Rejane Cerqueira (auditor)	\N	Usuario	23	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:39:48.133648
312	Criou usuário: Danielle Morato da Silva (auditor)	\N	Usuario	28	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:42:29.882924
317	Criou usuário: Kleidione Teixeira  de Moura (auditor)	\N	Usuario	33	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:45:02.430988
322	Criou usuário: Dila Fernandes  Barreto Sampaio (auditor)	\N	Usuario	38	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:47:52.87638
306	Criou usuário: Camila Serro Vargas (auditor)	\N	Usuario	22	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:38:01.227902
308	Criou usuário: Larissa Menezes Pacheco (auditor)	\N	Usuario	24	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:40:39.97076
313	Criou usuário: Vivian Lima Nascimento (auditor)	\N	Usuario	29	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:42:47.095444
318	Criou usuário: Laís Adalgiza  Vieira de Souza (auditor)	\N	Usuario	34	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-23 19:45:22.18596
323	Finalização Definitiva: Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026	\N	Aplicacao	15	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36	3	2	2026-01-24 04:08:18.458221
\.


--
-- Data for Name: notificacao; Type: TABLE DATA; Schema: public; Owner: qualigestor
--

COPY public.notificacao (id, titulo, mensagem, tipo, link, visualizada, data_visualizacao, usuario_id, data_criacao) FROM stdin;
\.


--
-- Data for Name: opcao_pergunta; Type: TABLE DATA; Schema: public; Owner: qualigestor
--

COPY public.opcao_pergunta (id, texto, valor, ordem, ativo, pergunta_id) FROM stdin;
1	Sim	1	1	t	1
2	Não	0	2	t	1
3	N.A.	0	3	t	1
4	Sim	1	1	t	2
5	Não	0	2	t	2
6	N.A.	0	3	t	2
7	1ª	0	1	t	3
8	2ª	0	2	t	3
9	Sim	1	1	t	4
10	Não	0	2	t	4
11	N.A.	0	3	t	4
12	Sim	1	1	t	5
13	Não	0	2	t	5
14	N.A.	0	3	t	5
15	Sim	1	1	t	6
16	Não	0	2	t	6
17	N.A.	0	3	t	6
18	Sim	1	1	t	7
19	Não	0	2	t	7
20	N.A.	0	3	t	7
21	Sim	1	1	t	8
22	Não	0	2	t	8
23	N.A.	0	3	t	8
24	Sim	1	1	t	9
25	Não	0	2	t	9
26	N.A.	0	3	t	9
27	Sim	1	1	t	10
28	Não	0	2	t	10
29	N.A.	0	3	t	10
30	Sim	1	1	t	11
31	Não	0	2	t	11
32	N.A.	0	3	t	11
33	Sim	1	1	t	12
34	Não	0	2	t	12
35	N.A.	0	3	t	12
36	Sim	1	1	t	13
37	Não	0	2	t	13
38	N.A.	0	3	t	13
39	Sim	1	1	t	14
40	Não	0	2	t	14
41	N.A.	0	3	t	14
42	Sim	1	1	t	15
43	Não	0	2	t	15
44	N.A.	0	3	t	15
45	Sim	1	1	t	16
46	Não	0	2	t	16
47	N.A.	0	3	t	16
48	Sim	1	1	t	17
49	Não	0	2	t	17
50	N.A.	0	3	t	17
51	Sim	1	1	t	18
52	Não	0	2	t	18
53	N.A.	0	3	t	18
54	Sim	1	1	t	19
55	Não	0	2	t	19
56	N.A.	0	3	t	19
57	Sim	1	1	t	20
58	Não	0	2	t	20
59	N.A.	0	3	t	20
60	Sim	1	1	t	21
61	Não	0	2	t	21
62	N.A.	0	3	t	21
63	Sim	1	1	t	23
64	Não	0	2	t	23
65	N.A.	0	3	t	23
66	Sim	1	1	t	24
67	Não	0	2	t	24
68	N.A.	0	3	t	24
69	Sim	1	1	t	25
70	Não	0	2	t	25
71	N.A.	0	3	t	25
72	Sim	1	1	t	26
73	Não	0	2	t	26
74	N.A.	0	3	t	26
75	Sim	1	1	t	27
76	Não	0	2	t	27
77	N.A.	0	3	t	27
78	Sim	1	1	t	28
79	Não	0	2	t	28
80	N.A.	0	3	t	28
81	Sim	1	1	t	29
82	Não	0	2	t	29
83	N.A.	0	3	t	29
84	Sim	1	1	t	30
85	Não	0	2	t	30
86	N.A.	0	3	t	30
87	Sim	1	1	t	31
88	Não	0	2	t	31
89	N.A.	0	3	t	31
90	Sim	1	1	t	32
91	Não	0	2	t	32
92	N.A.	0	3	t	32
93	Sim	1	1	t	33
94	Não	0	2	t	33
95	N.A.	0	3	t	33
96	Sim	1	1	t	34
97	Não	0	2	t	34
98	N.A.	0	3	t	34
99	Sim	1	1	t	36
100	Não	0	2	t	36
101	N.A.	0	3	t	36
102	Sim	1	1	t	37
103	Não	0	2	t	37
104	N.A.	0	3	t	37
105	Sim	1	1	t	38
106	Não	0	2	t	38
107	N.A.	0	3	t	38
108	Sim	1	1	t	39
109	Não	0	2	t	39
110	N.A.	0	3	t	39
111	Sim	1	1	t	40
112	Não	0	2	t	40
113	N.A.	0	3	t	40
114	Sim	1	1	t	41
115	Não	0	2	t	41
116	N.A.	0	3	t	41
117	Sim	1	1	t	42
118	Não	0	2	t	42
119	N.A.	0	3	t	42
120	Sim	1	1	t	43
121	Não	0	2	t	43
122	N.A.	0	3	t	43
123	Sim	1	1	t	44
124	Não	0	2	t	44
125	N.A.	0	3	t	44
126	Sim	1	1	t	45
127	Não	0	2	t	45
128	N.A.	0	3	t	45
129	Sim	1	1	t	46
130	Não	0	2	t	46
131	N.A.	0	3	t	46
132	Sim	1	1	t	47
133	Não	0	2	t	47
134	N.A.	0	3	t	47
135	Sim	1	1	t	48
136	Não	0	2	t	48
137	N.A.	0	3	t	48
138	Sim	1	1	t	49
139	Não	0	2	t	49
140	N.A.	0	3	t	49
144	Sim	1	1	t	51
145	Não	0	2	t	51
146	N.A.	0	3	t	51
147	Sim	1	1	t	52
148	Não	0	2	t	52
149	N.A.	0	3	t	52
150	Sim	1	1	t	53
151	Não	0	2	t	53
152	N.A.	0	3	t	53
153	Sim	1	1	t	54
154	Não	0	2	t	54
155	N.A.	0	3	t	54
156	Sim	1	1	t	55
157	Não	0	2	t	55
158	N.A.	0	3	t	55
159	Sim	1	1	t	56
160	Não	0	2	t	56
161	N.A.	0	3	t	56
162	Sim	1	1	t	57
163	Não	0	2	t	57
164	N.A.	0	3	t	57
165	Sim	1	1	t	58
166	Não	0	2	t	58
167	N.A.	0	3	t	58
168	Sim	1	1	t	59
169	Não	0	2	t	59
170	N.A.	0	3	t	59
171	Sim	1	1	t	60
172	Não	0	2	t	60
173	N.A.	0	3	t	60
174	Sim	1	1	t	61
175	Não	0	2	t	61
176	N.A.	0	3	t	61
177	Sim	1	1	t	63
178	Não	0	2	t	63
179	N.A.	0	3	t	63
180	Sim	1	1	t	64
181	Não	0	2	t	64
182	N.A.	0	3	t	64
183	Sim	1	1	t	65
184	Não	0	2	t	65
185	N.A.	0	3	t	65
186	Sim	1	1	t	66
187	Não	0	2	t	66
188	N.A.	0	3	t	66
189	Sim	1	1	t	67
190	Não	0	2	t	67
191	N.A.	0	3	t	67
192	Sim	1	1	t	68
193	Não	0	2	t	68
194	N.A.	0	3	t	68
195	Sim	1	1	t	69
196	Não	0	2	t	69
197	N.A.	0	3	t	69
198	Sim	1	1	t	70
199	Não	0	2	t	70
200	N.A.	0	3	t	70
201	Sim	1	1	t	71
202	Não	0	2	t	71
203	N.A.	0	3	t	71
204	Sim	1	1	t	72
205	Não	0	2	t	72
206	N.A.	0	3	t	72
207	Sim	1	1	t	73
208	Não	0	2	t	73
209	N.A.	0	3	t	73
210	Sim	1	1	t	75
211	Não	0	2	t	75
212	N.A.	0	3	t	75
213	Sim	1	1	t	76
214	Não	0	2	t	76
215	N.A.	0	3	t	76
216	Sim	1	1	t	77
217	Não	0	2	t	77
218	N.A.	0	3	t	77
219	Sim	1	1	t	78
220	Não	0	2	t	78
221	N.A.	0	3	t	78
222	Sim	1	1	t	79
223	Não	0	2	t	79
224	N.A.	0	3	t	79
225	Sim	1	1	t	80
226	Não	0	2	t	80
227	N.A.	0	3	t	80
228	Sim	1	1	t	81
229	Não	0	2	t	81
230	N.A.	0	3	t	81
231	Sim	1	1	t	82
232	Não	0	2	t	82
233	N.A.	0	3	t	82
234	Sim	1	1	t	83
235	Não	0	2	t	83
236	N.A.	0	3	t	83
237	Sim	1	1	t	84
238	Não	0	2	t	84
239	N.A.	0	3	t	84
240	Sim	1	1	t	85
241	Não	0	2	t	85
242	N.A.	0	3	t	85
243	Sim	1	1	t	86
244	Não	0	2	t	86
245	N.A.	0	3	t	86
246	Sim	1	1	t	88
247	Não	0	2	t	88
248	N.A.	0	3	t	88
249	Sim	1	1	t	89
250	Não	0	2	t	89
251	N.A.	0	3	t	89
252	Sim	1	1	t	90
253	Não	0	2	t	90
254	N.A.	0	3	t	90
255	Sim	1	1	t	91
256	Não	0	2	t	91
257	N.A.	0	3	t	91
258	Sim	1	1	t	92
259	Não	0	2	t	92
260	N.A.	0	3	t	92
261	Sim	1	1	t	93
262	Não	0	2	t	93
263	N.A.	0	3	t	93
264	Sim	1	1	t	94
265	Não	0	2	t	94
266	N.A.	0	3	t	94
267	Sim	1	1	t	95
268	Não	0	2	t	95
269	N.A.	0	3	t	95
270	Sim	1	1	t	96
271	Não	0	2	t	96
272	N.A.	0	3	t	96
273	Sim	1	1	t	97
274	Não	0	2	t	97
275	N.A.	0	3	t	97
276	Sim	1	1	t	99
277	Não	0	2	t	99
278	N.A.	0	3	t	99
279	Sim	1	1	t	100
280	Não	0	2	t	100
281	N.A.	0	3	t	100
282	Sim	1	1	t	101
283	Não	0	2	t	101
284	N.A.	0	3	t	101
285	Sim	1	1	t	102
286	Não	0	2	t	102
287	N.A.	0	3	t	102
288	Sim	1	1	t	103
289	Não	0	2	t	103
290	N.A.	0	3	t	103
291	Sim	1	1	t	105
292	Não	0	2	t	105
293	N.A.	0	3	t	105
294	Sim	1	1	t	106
295	Não	0	2	t	106
296	N.A.	0	3	t	106
297	Sim	1	1	t	107
298	Não	0	2	t	107
299	N.A.	0	3	t	107
300	Sim	1	1	t	108
301	Não	0	2	t	108
302	N.A.	0	3	t	108
303	Sim	1	1	t	109
304	Não	0	2	t	109
305	N.A.	0	3	t	109
306	Sim	1	1	t	110
307	Não	0	2	t	110
308	N.A.	0	3	t	110
309	Sim	1	1	t	112
310	Não	0	2	t	112
311	N.A.	0	3	t	112
312	Sim	1	1	t	113
313	Não	0	2	t	113
314	N.A.	0	3	t	113
315	Sim	1	1	t	114
316	Não	0	2	t	114
317	N.A.	0	3	t	114
321	Sim	1	1	t	116
322	Não	0	2	t	116
323	N.A.	0	3	t	116
324	Sim	1	1	t	117
325	Não	0	2	t	117
326	N.A.	0	3	t	117
327	Sim	1	1	t	118
328	Não	0	2	t	118
329	N.A.	0	3	t	118
330	Sim	1	1	t	119
331	Não	0	2	t	119
332	N.A.	0	3	t	119
333	Sim	1	1	t	120
334	Não	0	2	t	120
335	N.A.	0	3	t	120
336	Sim	1	1	t	121
337	Não	0	2	t	121
338	N.A.	0	3	t	121
339	Sim	1	1	t	122
340	Não	0	2	t	122
341	N.A.	0	3	t	122
342	Sim	1	1	t	123
343	Não	0	2	t	123
344	N.A.	0	3	t	123
345	Sim	1	1	t	124
346	Não	0	2	t	124
347	N.A.	0	3	t	124
348	Sim	1	1	t	125
349	Não	0	2	t	125
350	N.A.	0	3	t	125
351	Sim	1	1	t	126
352	Não	0	2	t	126
353	N.A.	0	3	t	126
354	Sim	1	1	t	127
355	Não	0	2	t	127
356	N.A.	0	3	t	127
357	Sim	1	1	t	128
358	Não	0	2	t	128
359	N.A.	0	3	t	128
360	Sim	1	1	t	129
361	Não	0	2	t	129
362	N.A.	0	3	t	129
363	Sim	1	1	t	130
364	Não	0	2	t	130
365	N.A.	0	3	t	130
366	Sim	1	1	t	131
367	Não	0	2	t	131
368	N.A.	0	3	t	131
369	Sim	1	1	t	132
370	Não	0	2	t	132
371	N.A.	0	3	t	132
375	Sim	1	1	t	134
376	Não	0	2	t	134
377	N.A.	0	3	t	134
378	Sim	1	1	t	135
379	Não	0	2	t	135
380	N.A.	0	3	t	135
381	Sim	1	1	t	136
382	Não	0	2	t	136
383	N.A.	0	3	t	136
384	Sim	1	1	t	137
385	Não	0	2	t	137
386	N.A.	0	3	t	137
387	Sim	1	1	t	138
388	Não	0	2	t	138
389	N.A.	0	3	t	138
390	Sim	1	1	t	139
391	Não	0	2	t	139
392	N.A.	0	3	t	139
396	Sim	1	1	t	141
397	Não	0	2	t	141
398	N.A.	0	3	t	141
399	Sim	1	1	t	142
400	Não	0	2	t	142
401	N.A.	0	3	t	142
402	Sim	1	1	t	143
403	Não	0	2	t	143
404	N.A.	0	3	t	143
405	Sim	1	1	t	144
406	Não	0	2	t	144
407	N.A.	0	3	t	144
408	Sim	1	1	t	145
409	Não	0	2	t	145
410	N.A.	0	3	t	145
411	Sim	1	1	t	146
412	Não	0	2	t	146
413	N.A.	0	3	t	146
414	Sim	1	1	t	148
415	Não	0	2	t	148
416	N.A.	0	3	t	148
417	Sim	1	1	t	149
418	Não	0	2	t	149
419	N.A.	0	3	t	149
420	Sim	1	1	t	150
421	Não	0	2	t	150
422	N.A.	0	3	t	150
423	Sim	1	1	t	151
424	Não	0	2	t	151
425	N.A.	0	3	t	151
426	Sim	1	1	t	152
427	Não	0	2	t	152
428	N.A.	0	3	t	152
429	Sim	1	1	t	153
430	Não	0	2	t	153
431	N.A.	0	3	t	153
441	Sim	1	1	t	162
442	Não	0	2	t	162
443	N.A.	0	3	t	162
444	Sim	1	1	t	163
445	Não	0	2	t	163
446	N.A.	0	3	t	163
447	Sim	1	1	t	164
448	Não	0	2	t	164
449	N.A.	0	3	t	164
450	Sim	1	1	t	165
451	Não	0	2	t	165
452	N.A.	0	3	t	165
453	Sim	1	1	t	166
454	Não	0	2	t	166
455	N.A.	0	3	t	166
456	Sim	1	1	t	167
457	Não	0	2	t	167
458	N.A.	0	3	t	167
459	Sim	1	1	t	168
460	Não	0	2	t	168
461	N.A.	0	3	t	168
462	Sim	1	1	t	169
463	Não	0	2	t	169
464	N.A.	0	3	t	169
465	Sim	1	1	t	170
466	Não	0	2	t	170
467	N.A.	0	3	t	170
468	Sim	1	1	t	171
469	Não	0	2	t	171
470	N.A.	0	3	t	171
471	Sim	1	1	t	172
472	Não	0	2	t	172
473	N.A.	0	3	t	172
474	Sim	1	1	t	173
475	Não	0	2	t	173
476	N.A.	0	3	t	173
477	Sim	1	1	t	174
478	Não	0	2	t	174
479	N.A.	0	3	t	174
480	Sim	1	1	t	175
481	Não	0	2	t	175
482	N.A.	0	3	t	175
483	Sim	1	1	t	176
484	Não	0	2	t	176
485	N.A.	0	3	t	176
486	Sim	1	1	t	177
487	Não	0	2	t	177
488	N.A.	0	3	t	177
489	Sim	1	1	t	178
490	Não	0	2	t	178
491	N.A.	0	3	t	178
492	Sim	1	1	t	179
493	Não	0	2	t	179
494	N.A.	0	3	t	179
495	Sim	1	1	t	180
496	Não	0	2	t	180
497	N.A.	0	3	t	180
498	Sim	1	1	t	181
499	Não	0	2	t	181
500	N.A.	0	3	t	181
\.


--
-- Data for Name: pergunta; Type: TABLE DATA; Schema: public; Owner: qualigestor
--

COPY public.pergunta (id, texto, tipo, obrigatoria, permite_observacao, peso, ordem, ativo, exige_foto_se_nao_conforme, configuracoes, topico_id, criado_em, criterio_foto) FROM stdin;
1	teste 1	SIM_NAO_NA	t	t	1	1	t	t	\N	1	2025-12-17 15:07:07.202986	nenhuma
2	teste 2	SIM_NAO_NA	t	t	1	2	t	t	\N	1	2025-12-17 15:07:15.779623	nenhuma
133	Descrever aqui, com maiores detalhes, os óbices encontrados.	TEXTO_LONGO	t	t	0	18	t	f	\N	13	2026-01-02 15:53:10.309055	opcional
3	1º ou 2º Visita?	MULTIPLA_ESCOLHA	t	t	0	1	f	f	\N	2	2026-01-02 15:23:41.359809	nenhuma
5	Teto, forro e paredes de cor clara, de fácil limpeza, livres de rachaduras, bolores, infiltrações e falhas?	SIM_NAO_NA	t	t	1	2	t	t	\N	3	2026-01-02 15:24:27.633854	opcional
6	As áreas previstas para manipulação dos alimentos, encontram-se bem definidas, com separação por meio de barreiras físicas ou técnicas?	SIM_NAO_NA	t	t	1	3	t	t	\N	3	2026-01-02 15:24:34.475486	opcional
7	Ventilação adequada em todas as áreas, garantindo conforto térmico?	SIM_NAO_NA	t	t	1	4	t	t	\N	3	2026-01-02 15:24:43.095156	opcional
8	Equipamentos de climatização em bom estado de conservação e limpeza?	SIM_NAO_NA	t	t	1	5	t	t	\N	3	2026-01-02 15:24:49.892969	opcional
9	Presença de sistema de exaustão e/ou insuflamento com troca de ar capaz de prevenir contaminações?	SIM_NAO_NA	t	t	1	6	t	t	\N	3	2026-01-02 15:24:58.343556	opcional
11	Piso de material liso, cor clara, de fácil limpeza, antiderrapante e em adequado estado de conservação?	SIM_NAO_NA	t	t	1	8	t	t	\N	3	2026-01-02 15:25:11.628715	opcional
12	Montacarga e estruturas auxiliares em adequado estado de conservação?	SIM_NAO_NA	t	t	1	9	t	t	\N	3	2026-01-02 15:25:19.276655	opcional
13	Possui pias exclusivas para lavagem das mãos na área de produção em numero suficiente e com torneiras de acionamento automático?	SIM_NAO_NA	t	t	1	10	t	t	\N	3	2026-01-02 15:25:24.818679	opcional
14	Caixas de gordura apresentam-se instaladas fora da área de produção e encontram-se em bom estado de conservação?	SIM_NAO_NA	t	t	1	11	t	t	\N	3	2026-01-02 15:25:32.803507	opcional
15	Ralos e grelhas apresentam tampas com dispositivo de fechamento e/ou tela milimétrica adaptada? Encontra-se em bom estado de conservação (sem ferrugem ou rachaduras)?	SIM_NAO_NA	t	t	1	12	t	t	\N	3	2026-01-02 15:25:37.738661	opcional
17	Tomadas são identificadas conforme previsto na NR 10?	SIM_NAO_NA	t	t	1	14	t	t	\N	3	2026-01-02 15:25:51.277294	opcional
44	São armazenadas amostras de contra prova de alimentos por 72h ou conforme o prazo previsto em legislação local?	SIM_NAO_NA	t	t	1	9	t	t	\N	5	2026-01-02 15:35:28.195293	opcional
46	Gelo usado em contato direto com alimentos e bebidas de fonte segura e aprovada?	SIM_NAO_NA	t	t	1	11	t	t	\N	5	2026-01-02 15:35:39.808188	opcional
47	Existem filtros de água? Os filtros são limpos regularmente?	SIM_NAO_NA	t	t	1	12	t	t	\N	5	2026-01-02 15:35:45.333711	opcional
16	Iluminação adequada para a atividade desenvolvida, com lâmpadas dotadas de sistema de proteção (contra queda/explosão)?	SIM_NAO_NA	t	t	1	13	t	t	\N	3	2026-01-02 15:25:45.083862	opcional
18	Instalações elétricas encontram-se em bom estado de conservação, sem fios aparentes ou descascados?	SIM_NAO_NA	t	t	1	15	t	t	\N	3	2026-01-02 15:25:56.984725	opcional
155	TREINAMENTO -  Descrever a temática abordada, metodologia utilizada, % do efetivo participante e as limitações de conhecimento apontadas pelos profissionais do rancho.	TEXTO_LONGO	t	t	0	8	f	f	\N	16	2026-01-02 15:57:41.337623	nenhuma
4	Portas encontram-se em bom estado de conservação (livre de rachaduras, bolor, infiltrações e falhas)? \r\n São de material de fácil limpeza e de cor clara? \r\n Apresentam protetor de rodapés e fechamento automático (molas)?	SIM_NAO_NA	t	t	1	1	t	t	\N	3	2026-01-02 15:24:14.443486	opcional
179	Levantou no horário correto?	SIM_NAO_NA	t	t	1	1	t	f	\N	21	2026-01-17 04:29:02.639842	opcional
181	Escovou os dentes antes do café?	SIM_NAO_NA	t	t	1	3	t	f	\N	21	2026-01-17 04:29:35.705837	opcional
180	Arrumou a cama?	SIM_NAO_NA	t	t	1	2	t	f	\N	21	2026-01-17 04:29:20.326259	opcional
10	Janelas, portas e aberturas, incluindo sistema de exaustão e áreas de armazenamento apresentam telas milimetradas para  proteção contra pragas e vetores, de material de fácil limpeza e em bom estado de conservação?	SIM_NAO_NA	t	t	1	7	t	t	\N	3	2026-01-02 15:25:04.616893	opcional
19	Os extintores estão lacrados, dentro da validade e com o selo de conformidade concedida por órgão credenciado pelo sistema brasileiro de certificação do INMETRO?	SIM_NAO_NA	t	t	1	16	t	t	\N	3	2026-01-02 15:26:04.978948	opcional
20	Possui identificação das saídas de emergência?	SIM_NAO_NA	t	t	1	17	t	t	\N	3	2026-01-02 15:26:11.411841	opcional
21	Há  local  apropriado  para  a  estocagem  de  materiais  inflamáveis,  químicos,  ácidos e corrosivos  (inciso  XIII,  art.  32;  e  art.  152,  ambos  do  RADA;  letra  “b”,  item  4.2  da ICA 174-1/2007; e item 10.11 do MCA 67-1/2007).	SIM_NAO_NA	t	t	1	18	t	t	\N	3	2026-01-02 15:26:18.991401	opcional
22	Descrever aqui, com maiores detalhes, os óbices encontrados.	TEXTO_LONGO	t	t	0	19	t	f	\N	3	2026-01-02 15:26:57.244496	opcional
23	Os uniformes são adequados para área de manipulação de alimentos (inclusive sapatos) considerando o preconizado no novo RUMAER? Encontram se limpos e em bom estado de conservação?	SIM_NAO_NA	t	t	1	1	t	t	\N	4	2026-01-02 15:27:34.128452	opcional
24	Utilizam corretamente a proteção para os cabelos (touca)?	SIM_NAO_NA	t	t	1	2	t	t	\N	4	2026-01-02 15:29:17.405737	opcional
25	Possuem hábitos adequados de higiene pessoal (unhas curtas, sem esmalte ou base, sem maquiagem e sem barba)?	SIM_NAO_NA	t	t	1	3	t	t	\N	4	2026-01-02 15:29:22.454358	opcional
26	Quando o funcionário possui corte ou ferida é utilizado luvas ou dedeiras para evitar possível contaminação?	SIM_NAO_NA	t	t	1	4	t	t	\N	4	2026-01-02 15:29:31.006482	opcional
27	O controle da saúde dos manipuladores ocorre anualmente. Está em dia (com todos as datas de inspeção de todos os militares em dia) e está registrado e arquivado no Serviço de Alimentação da OM?	SIM_NAO_NA	t	t	1	5	t	t	\N	4	2026-01-02 15:29:41.298907	opcional
28	Possuem EPI em estoque e o material está disponível para o efetivo?	SIM_NAO_NA	t	t	1	6	t	t	\N	4	2026-01-02 15:29:49.087651	opcional
29	Fazem uso correto  de EPIs ( óculos, avental, luvas descartáveis/ térmicas/malha de aço) e os mesmos são mantidos em adequado estado de conservação?	SIM_NAO_NA	t	t	1	7	t	t	\N	4	2026-01-02 15:29:55.856981	opcional
30	Presença de material para a higiene das mãos (sabão bactericida, papel tolha branco e álcool gel) junto as pias exclusivas para higienização das mãos?	SIM_NAO_NA	t	t	1	8	t	t	\N	4	2026-01-02 15:30:04.625261	opcional
31	Ausência de utilização de celular, fone de ouvido e outros equipamentos sonoros durante o serviço?	SIM_NAO_NA	t	t	1	9	t	t	\N	4	2026-01-02 15:30:14.778689	opcional
32	Roupas e objetos pessoais guardados em local específico para este fim, fora da área de manipulação?	SIM_NAO_NA	t	t	1	10	t	t	\N	4	2026-01-02 15:30:19.865538	opcional
33	Existem cartazes de orientação aos manipuladores sobre a correta lavagem e antissepsia das mãos e demais hábitos de higiene, em locais de fácil visualização, inclusive nas instalações sanitárias e lavatórios?	SIM_NAO_NA	t	t	1	11	t	t	\N	4	2026-01-02 15:30:28.258831	opcional
34	Funcionários responsáveis pela atividade de higienização das instalações utilizam uniformes apropriados e diferenciados daqueles usados na manipulação de alimentos?	SIM_NAO_NA	t	t	1	12	t	t	\N	4	2026-01-02 15:32:41.224522	opcional
35	Descrever aqui, com maiores detalhes, os óbices encontrados.	TEXTO_LONGO	t	t	0	13	t	f	\N	4	2026-01-02 15:32:54.439493	opcional
36	Procedimento de higienização dos hortifrutis é realizado corretamente (diluição, produto, tempo de ação, corretos)?	SIM_NAO_NA	t	t	1	1	t	t	\N	5	2026-01-02 15:34:19.026591	opcional
37	Placas de corte estão limpas?	SIM_NAO_NA	t	t	1	2	t	t	\N	5	2026-01-02 15:34:24.032635	opcional
38	Procedimento de descongelamento é realizado corretamente?\r\nEstá identificado com etiqueta de descongelamento?	SIM_NAO_NA	t	t	1	3	t	t	\N	5	2026-01-02 15:34:31.918239	opcional
39	Fluxos e procedimentos seguros, eliminando os riscos de contaminação cruzada?	SIM_NAO_NA	t	t	1	4	t	t	\N	5	2026-01-02 15:34:38.167673	opcional
40	O arroz e feijão são lavados a cada utilização?	SIM_NAO_NA	t	t	1	5	t	t	\N	5	2026-01-02 15:34:51.461856	opcional
41	As preparações prontas estão cobertas, tampadas e em temperatura correta?	SIM_NAO_NA	t	t	1	6	t	t	\N	5	2026-01-02 15:34:57.061817	opcional
42	Temperatura de manutenção adequada dos alimentos prontos no passthrough ( > 65°C quente) e (< 10°C frio)?	SIM_NAO_NA	t	t	1	7	t	t	\N	5	2026-01-02 15:35:02.803838	opcional
43	Temperatura de manutenção adequada dos alimentos prontos nos balcões  ( > 60°C quente) e (< 10°C frio)?	SIM_NAO_NA	t	t	1	8	t	t	\N	5	2026-01-02 15:35:22.802354	opcional
45	Existência de reservatório de água acessível dotado de tampas, em satisfatória condição de uso, livre de vazamentos, infiltrações e descascamentos? (Verificar com o responsável pela manutenção se a instalação hidráulica está com volume, pressão e temperatura adequados - anotar no campo de observação estas informações ou a não possibilidade de contato com o responsável).	SIM_NAO_NA	t	t	1	10	t	t	\N	5	2026-01-02 15:35:34.617974	opcional
48	O reaproveitamento de sobras limpas é adequado?	SIM_NAO_NA	t	t	1	13	t	t	\N	5	2026-01-02 15:35:52.135062	opcional
49	Visitantes cumprem os requisitos de higiene e saúde estabelecidos para os manipuladores?	SIM_NAO_NA	t	t	1	14	t	t	\N	5	2026-01-02 15:36:00.673094	opcional
50	Descrever aqui, com maiores detalhes, os óbices encontrados.	TEXTO_LONGO	t	t	0	15	t	f	\N	5	2026-01-02 15:36:05.602354	opcional
51	Estão presentes todos os materiais de limpeza (deterg., deseng., sanitiz.) e são usados de acordo com a instrução do fabricante?	SIM_NAO_NA	t	t	1	1	t	t	\N	6	2026-01-02 15:37:34.401862	opcional
52	Superfície de manipulação, preparo e distribuição dos alimentos  possui material liso e lavável, sem risco de contaminação?	SIM_NAO_NA	t	t	1	2	t	t	\N	6	2026-01-02 15:37:42.092687	opcional
53	Esponjas/ Fibras estão em boas condições de uso?	SIM_NAO_NA	t	t	1	3	t	t	\N	6	2026-01-02 15:37:47.769459	opcional
54	Ausência de esponja imersa em solução detergente?	SIM_NAO_NA	t	t	1	4	t	t	\N	6	2026-01-02 15:37:56.369611	opcional
55	Fazem uso de pano descartável?	SIM_NAO_NA	t	t	1	5	t	t	\N	6	2026-01-02 15:38:04.072073	opcional
56	MOP/esfregão/pano de chão estão limpos?	SIM_NAO_NA	t	t	1	6	t	t	\N	6	2026-01-02 15:38:17.434655	opcional
57	Os tetos, portas, paredes, pisos, janelas e telas de todas as áreas estão limpas?	SIM_NAO_NA	t	t	1	7	t	t	\N	6	2026-01-02 15:38:22.626873	opcional
58	O acesso a cozinha garante a proteção contra a entrada de pragas ou animais?	SIM_NAO_NA	t	t	1	8	t	t	\N	6	2026-01-02 15:38:27.378609	opcional
59	Produtos de limpeza (detergentes e desinfetantes) com registro na ANVISA/MS?	SIM_NAO_NA	t	t	1	9	t	t	\N	6	2026-01-02 15:38:32.284851	opcional
60	Refeitório limpo e organizado?	SIM_NAO_NA	t	t	1	10	t	t	\N	6	2026-01-02 15:38:36.68947	opcional
61	Utensílios utilizados na higienização de instalações são distintos daqueles usados para higienização das partes dos equipamentos e utensílios que entrem em contato com o alimento?	SIM_NAO_NA	t	t	1	11	t	t	\N	6	2026-01-02 15:38:41.262119	opcional
62	Descrever aqui, com maiores detalhes, os óbices encontrados.	TEXTO_LONGO	t	t	0	12	t	f	\N	6	2026-01-02 15:39:03.990427	opcional
63	Os pisos, paredes e prateleiras encontram-se limpos?	SIM_NAO_NA	t	t	1	1	t	t	\N	7	2026-01-02 15:41:45.076106	opcional
64	As caixas plásticas estão limpas?	SIM_NAO_NA	t	t	1	2	t	t	\N	7	2026-01-02 15:41:51.502633	opcional
65	A armazenagem segue o PVPS (primeiro que vence, primeiro que sai)?	SIM_NAO_NA	t	t	1	3	t	t	\N	7	2026-01-02 15:41:57.739481	opcional
66	Os produtos estão dentro do prazo de validade?	SIM_NAO_NA	t	t	1	4	t	t	\N	7	2026-01-02 15:42:04.465893	opcional
67	Os produtos encontram-se com rotulagem completa?	SIM_NAO_NA	t	t	1	5	t	t	\N	7	2026-01-02 15:42:10.337649	opcional
68	Produtos e embalagens mantidos devidamente fechados e protegidos?	SIM_NAO_NA	t	t	1	6	t	t	\N	7	2026-01-02 15:42:15.163099	opcional
69	Produtos armazenados sob estrados e/ou prateleiras?	SIM_NAO_NA	t	t	1	7	t	t	\N	7	2026-01-02 15:42:19.904288	opcional
70	Cantos e paredes desobstruídos, sem produtos encostados?	SIM_NAO_NA	t	t	1	8	t	t	\N	7	2026-01-02 15:42:26.211188	opcional
71	As caixas plásticas e monoblocos foram higienizados antes da utilização?	SIM_NAO_NA	t	t	1	9	t	t	\N	7	2026-01-02 15:43:00.653422	opcional
72	Os produtos recebidos foram retirados das embalagens inapropriadas (caixotes de madeira), para a triagem, lavados e acondicionados em  caixas plásticas  posteriormente?	SIM_NAO_NA	t	t	1	10	t	t	\N	7	2026-01-02 15:43:07.423094	opcional
73	Os alimentos encontram-se armazenados separados dos produtos de higienização e materiais descartáveis?	SIM_NAO_NA	t	t	1	11	t	t	\N	7	2026-01-02 15:43:12.305155	opcional
74	Descrever aqui, com maiores detalhes, os óbices encontrados.	TEXTO_LONGO	t	t	0	12	t	f	\N	7	2026-01-02 15:43:24.806014	opcional
75	Os pisos, paredes e prateleiras encontram-se limpos?	SIM_NAO_NA	t	t	1	1	t	t	\N	8	2026-01-02 15:45:53.506875	opcional
76	Caixas plásticas foram higienizados antes da utilização?	SIM_NAO_NA	t	t	1	2	t	t	\N	8	2026-01-02 15:45:58.533513	opcional
77	Os produtos recebidos foram retirados das embalagens grotescas inapropriadas, para a triagem, lavados e acondicionados em  posteriormente?	SIM_NAO_NA	t	t	1	3	t	t	\N	8	2026-01-02 15:46:03.75538	opcional
78	Na câmara, os produtos em preparação, os produtos prontos e os gêneros recém recebidos são conservados em prateleira na disposição prevista em legislação (alimentos prontos nas prateleiras de cima / alimentos pré-preparados nas prateleiras do meio / alimentos crus na prateleira inferior)?	SIM_NAO_NA	t	t	1	4	t	t	\N	8	2026-01-02 15:46:08.549999	opcional
79	Na presença de caixas de papelão, as mesmas encontram-se envoltas em plástico transparente, em bom estado de conservação, limpas e livre de bolor?	SIM_NAO_NA	t	t	1	6	t	t	\N	8	2026-01-02 15:46:13.334535	opcional
80	Produtos e embalagens mantidos devidamente fechados e protegidos?	SIM_NAO_NA	t	t	1	7	t	t	\N	8	2026-01-02 15:46:17.541834	opcional
81	Preparações e sobras estão identificadas (nome e validade)?	SIM_NAO_NA	t	t	1	8	t	t	\N	8	2026-01-02 15:46:21.992462	opcional
82	Ausência de ralos no interior das câmaras frigoríficas?	SIM_NAO_NA	t	t	1	9	t	t	\N	8	2026-01-02 15:46:27.460523	opcional
83	Ausência de alimentos deteriorados nas geladeiras e câmaras frigoríficas?	SIM_NAO_NA	t	t	1	10	t	t	\N	8	2026-01-02 15:46:32.382034	opcional
84	Câmara de congelamento em funcionamento adequado (temp.: - 12° a - 18°C)?	SIM_NAO_NA	t	t	1	11	t	t	\N	8	2026-01-02 15:46:36.925886	opcional
85	Câmara de resfriamento em funcionamento adequado (temp.: 4° a 10°C)?	SIM_NAO_NA	t	t	1	12	t	t	\N	8	2026-01-02 15:46:42.02332	opcional
86	O sistema de refrigeração está livre de sujidades?	SIM_NAO_NA	t	t	1	13	t	t	\N	8	2026-01-02 15:46:49.083769	opcional
87	Descrever aqui, com maiores detalhes, os óbices\r\n encontrados.	TEXTO_LONGO	t	t	0	14	t	f	\N	8	2026-01-02 15:46:57.457483	opcional
88	Os equipamentos da linha de produção estão em número adequado à atividade, e estão dispostos de forma a permitir\r\nfácil acesso e higienização adequada?	SIM_NAO_NA	t	t	1	1	t	t	\N	9	2026-01-02 15:47:47.657492	opcional
89	Os equipamentos que necessitam de limpeza orgânica (por meio da contratação de serviço) estão em boas condições de uso?	SIM_NAO_NA	t	t	1	2	t	t	\N	9	2026-01-02 15:48:07.083113	opcional
90	Os demais equipamentos  da cozinha são de material adequado, estão limpos e em perfeitas condições de funcionamento?	SIM_NAO_NA	t	t	1	3	t	t	\N	9	2026-01-02 15:48:12.319909	opcional
91	Os utensílios estão limpos, de material adequado e em perfeitas condições de uso?	SIM_NAO_NA	t	t	1	4	t	t	\N	9	2026-01-02 15:48:17.647423	opcional
92	Equipamentos e utensílios guardados corretamente?	SIM_NAO_NA	t	t	1	5	t	t	\N	9	2026-01-02 15:48:22.565054	opcional
93	Máquinas de lavar com utilização de água quente?	SIM_NAO_NA	t	t	1	6	t	t	\N	9	2026-01-02 15:48:27.857535	opcional
94	Máquinas de lavar (cortinas, reservatório etc.) em boas condições de limpeza?	SIM_NAO_NA	t	t	1	7	t	t	\N	9	2026-01-02 15:48:32.631799	opcional
95	Presença de detergente e secante devidamente instalados nas máquinas?	SIM_NAO_NA	t	t	1	8	t	t	\N	9	2026-01-02 15:48:37.340792	opcional
96	Ausência de equipamentos fora de uso ou quebrado?	SIM_NAO_NA	t	t	1	9	t	t	\N	9	2026-01-02 15:48:41.791864	opcional
97	Mobiliário em número suficiente, de material apropriado, resistentes, impermeáveis, em adequado estado de conservação, com superfícies íntegras?	SIM_NAO_NA	t	t	1	10	t	t	\N	9	2026-01-02 15:48:47.731499	opcional
98	Descrever aqui, com maiores detalhes, os óbices encontrados.	TEXTO_LONGO	t	t	0	11	t	f	\N	9	2026-01-02 15:48:56.25878	opcional
99	As preparações transportadas estão acondicionadas corretamente em caixas térmicas?	SIM_NAO_NA	t	t	1	1	t	t	\N	10	2026-01-02 15:49:15.459022	opcional
100	As preparações sofrem reaquecimento assim que chegam a unidade?	SIM_NAO_NA	t	t	1	2	t	t	\N	10	2026-01-02 15:49:21.068057	opcional
101	As preparações estão na temperatura adequada no momento da distribuição?	SIM_NAO_NA	t	t	1	3	t	t	\N	10	2026-01-02 15:49:25.667172	opcional
102	Os veículos de transporte são utilizados apenas para alimentos?	SIM_NAO_NA	t	t	1	4	t	t	\N	10	2026-01-02 15:49:29.998881	opcional
103	Os veículos de transporte estão higienizados?	SIM_NAO_NA	t	t	1	5	t	t	\N	10	2026-01-02 15:49:34.458816	opcional
104	Descrever aqui, com maiores detalhes, os óbices encontrados.	TEXTO_LONGO	t	t	0	6	t	f	\N	10	2026-01-02 15:49:45.584171	opcional
105	O lixo se encontra em área limpa, organizada e isolada?	SIM_NAO_NA	t	t	1	1	t	t	\N	11	2026-01-02 15:50:06.670351	opcional
106	Ausência de lixo na área externa?	SIM_NAO_NA	t	t	1	2	t	t	\N	11	2026-01-02 15:50:11.604744	opcional
107	As lixeiras internas estão tampadas,  limpas, forradas e sem excesso de lixo?	SIM_NAO_NA	t	t	1	3	t	t	\N	11	2026-01-02 15:50:16.333505	opcional
108	As lixeiras internas possuem tampa e acionamento por pedal?	SIM_NAO_NA	t	t	1	4	t	t	\N	11	2026-01-02 15:50:22.451258	opcional
109	Resíduo orgânico armazenado em área refrigerada?	SIM_NAO_NA	t	t	1	5	t	t	\N	11	2026-01-02 15:50:27.009856	opcional
110	Presença de coleta seletiva?	SIM_NAO_NA	t	t	1	7	t	t	\N	11	2026-01-02 15:50:31.517623	opcional
111	Descrever aqui, com maiores detalhes, os óbices encontrados.	TEXTO_LONGO	t	t	0	9	t	f	\N	11	2026-01-02 15:50:40.625689	opcional
112	Ausência de pragas e vetores ou os seus vestígios?	SIM_NAO_NA	t	t	1	1	t	t	\N	12	2026-01-02 15:50:56.559283	opcional
113	Ausência de telas rasgadas, ralos abertos e lixo exposto?	SIM_NAO_NA	t	t	1	2	t	t	\N	12	2026-01-02 15:51:02.861413	opcional
114	Presença de registro em dia de aplicação do serviço do controle de pragas?	SIM_NAO_NA	t	t	1	3	t	t	\N	12	2026-01-02 15:51:08.630508	opcional
116	Possui manual de boas práticas de fabricação atualizado?	SIM_NAO_NA	t	t	1	1	t	t	\N	13	2026-01-02 15:51:34.007596	opcional
117	A unidade possui termômetro para realizar os registros?	SIM_NAO_NA	t	t	1	2	t	t	\N	13	2026-01-02 15:51:43.834216	opcional
118	São realizados registros de monitoramento de temperatura de alimentos e equipamentos?	SIM_NAO_NA	t	t	1	3	t	t	\N	13	2026-01-02 15:51:49.026293	opcional
119	São realizados registros de monitoramento de higienização de ambientes?	SIM_NAO_NA	t	t	1	4	t	t	\N	13	2026-01-02 15:51:53.25036	opcional
120	São realizados registros de monitoramento de higienização de equipamentos?	SIM_NAO_NA	t	t	1	5	t	t	\N	13	2026-01-02 15:51:58.143745	opcional
121	São realizados registros diários do acompanhamento de Resta ingesta ?	SIM_NAO_NA	t	t	1	6	t	t	\N	13	2026-01-02 15:52:02.920253	opcional
122	Existência de registro da execução de higienização semestral dos reservatórios de água? (Na inexistência de laudos descrever na observação como é realizado o processo de higienização dos reservatórios).	SIM_NAO_NA	t	t	1	7	t	t	\N	13	2026-01-02 15:52:08.042887	opcional
123	Existência de registros de manutenção preventiva dos equipamentos?	SIM_NAO_NA	t	t	1	8	t	t	\N	13	2026-01-02 15:52:13.219003	opcional
124	Existência de registros de manutenção corretiva dos equipamentos?	SIM_NAO_NA	t	t	1	9	t	t	\N	13	2026-01-02 15:52:22.526796	opcional
125	Existência de registros de manutenção, operação e controle dos sistemas de ar condicionado (lei 13.589/2018)?	SIM_NAO_NA	t	t	1	10	t	t	\N	13	2026-01-02 15:52:27.904623	opcional
126	Existência de registros de calibração dos termômetros de medição?	SIM_NAO_NA	t	t	1	11	t	t	\N	13	2026-01-02 15:52:32.269112	opcional
127	Existência de registros de calibração das balanças?	SIM_NAO_NA	t	t	1	12	t	t	\N	13	2026-01-02 15:52:37.576734	opcional
128	Existência do quadro de avisos fixado em área de grande circulação e com informações atualizadas?	SIM_NAO_NA	t	t	1	13	t	t	\N	13	2026-01-02 15:52:43.011104	opcional
129	Existência de registro de limpeza das caixas de gordura?	SIM_NAO_NA	t	t	1	14	t	t	\N	13	2026-01-02 15:52:47.709612	opcional
130	Existência de registro das análises de potabilidade da água?	SIM_NAO_NA	t	t	1	15	t	t	\N	13	2026-01-02 15:52:53.60277	opcional
131	Existência de registro da validade e substituição dos filtros (bebedouros)?	SIM_NAO_NA	t	t	1	16	t	t	\N	13	2026-01-02 15:52:57.951378	opcional
132	Existência de registro dos caso suspeitos de Doença Transmitida por Alimentos? Em caso positivo, anexar o registro.	SIM_NAO_NA	t	t	1	17	t	t	\N	13	2026-01-02 15:53:02.433019	opcional
134	Os laudos dos alimentos apresentaram resultados satisfatórios?	SIM_NAO_NA	t	t	1	1	t	t	\N	14	2026-01-02 15:53:53.995776	opcional
135	Os laudos dos swabs de manipuladores apresentaram resultados satisfatórios?	SIM_NAO_NA	t	t	1	2	t	t	\N	14	2026-01-02 15:53:58.778052	opcional
136	Os laudos dos swabs de equipamentos apresentaram resultados satisfatórios?	SIM_NAO_NA	t	t	1	3	t	t	\N	14	2026-01-02 15:54:04.052287	opcional
137	Os laudos dos swabs de utensílios apresentaram resultados satisfatórios?	SIM_NAO_NA	t	t	1	4	t	t	\N	14	2026-01-02 15:54:09.611548	opcional
138	Os laudos dos swabs de superfície apresentaram resultados satisfatórios?	SIM_NAO_NA	t	t	1	5	t	t	\N	14	2026-01-02 15:54:15.255093	opcional
139	O laudo da água apresentou resultado satisfatório?	SIM_NAO_NA	t	t	1	6	t	t	\N	14	2026-01-02 15:54:20.402651	opcional
140	Descrever aqui quais amostras apresentaram resultado insatisfatório e o que foi apresentado.	TEXTO_LONGO	t	t	0	7	t	f	\N	14	2026-01-02 15:54:25.043973	opcional
141	Vestiários e sanitários respeitam as exigências de instalações gerais (piso, teto, paredes e janelas)?	SIM_NAO_NA	t	t	1	1	t	t	\N	15	2026-01-02 15:55:42.035105	opcional
142	Vestiários e sanitários são servidos de água corrente?	SIM_NAO_NA	t	t	1	2	t	t	\N	15	2026-01-02 15:55:46.333296	opcional
143	Vasos sanitários e chuveiros em número suficiente? Obs.:1 para cada 20 pessoas	SIM_NAO_NA	t	t	1	3	t	t	\N	15	2026-01-02 15:55:50.741918	opcional
144	Instalações sanitárias dotadas de lavatórios e de produtos destinados a higiene pessoal tais como:\r\n- Papel higiênico;\r\n- Sabonete líquido ;\r\n- Toalhas de papel não reciclado ou outro sistema higiênico e seguro para secagem das mãos; e\r\n- Coletores dos resíduos (lixeiras) dotados de tampa e acionados sem contato manual.	SIM_NAO_NA	t	t	1	4	t	t	\N	15	2026-01-02 15:55:56.847702	opcional
145	Vestiários dotados de armários em número suficiente?	SIM_NAO_NA	t	t	1	5	t	t	\N	15	2026-01-02 15:56:01.92387	opcional
146	Vestiários apresentam bom estado de conservação?	SIM_NAO_NA	t	t	1	6	t	t	\N	15	2026-01-02 15:56:07.646375	opcional
147	Descrever aqui, com maiores detalhes, os óbices encontrados.	TEXTO_LONGO	t	t	0	7	t	f	\N	15	2026-01-02 15:56:16.357597	opcional
148	Possui cardápio semanal exposto em local visível e de fácil acesso no rancho?	SIM_NAO_NA	t	t	1	1	t	t	\N	16	2026-01-02 15:56:37.528652	opcional
149	Existem Fichas técnicas  para as preparações previstas em cardápio (especificar quem realiza a elaboração e atualização dessas fichas na OM)?	SIM_NAO_NA	t	t	1	2	t	t	\N	16	2026-01-02 15:56:42.986732	opcional
150	Os cardápios semanais são disponibilizados antecipadamente ao estoque e à cozinha de forma que sejam efetuados ajustes antes da aprovação final.	SIM_NAO_NA	t	t	1	3	t	t	\N	16	2026-01-02 15:56:47.828882	opcional
151	Para os casos de dietas especiais, direcionada aos militares que possuem algum tipo de restrição alimentar, é  elaborado uma cardápio mínimo com adaptações da dieta de acordo com a comorbidade base.	SIM_NAO_NA	t	t	1	4	t	t	\N	16	2026-01-02 15:56:52.713391	opcional
152	É realizado promoção da saúde e prevenção de doenças por meio de atividades ou campanhas direcionados ao efetivo da OM.	SIM_NAO_NA	t	t	1	5	t	t	\N	16	2026-01-02 15:56:57.664659	opcional
153	O resultado do indicador de qualidade dos cardápios foi satisfatório?	SIM_NAO_NA	t	t	1	6	t	t	\N	16	2026-01-02 15:57:02.845892	opcional
115	Descrever aqui, com maiores detalhes, os óbices encontrados.	TEXTO_LONGO	t	t	0	4	t	f	\N	12	2026-01-02 15:51:15.678604	opcional
154	Descrever aqui, com maiores detalhes, os óbices encontrados.	TEXTO_LONGO	t	t	0	7	t	t	\N	16	2026-01-02 15:57:07.755159	opcional
158	Nome do Militar Responsável pela visita	TEXTO_LONGO	t	t	0	1	t	f	\N	18	2026-01-02 15:58:36.84603	opcional
159	Assinatura do Militar Responsável pela visita	ASSINATURA	t	t	0	2	t	f	\N	18	2026-01-02 15:58:48.157007	opcional
160	Nome do consultor Responsável pela visita	TEXTO_LONGO	t	t	0	3	t	f	\N	18	2026-01-02 16:00:21.727149	opcional
161	Assinatura do consultor Responsável pela visita	ASSINATURA	t	t	0	4	t	f	\N	18	2026-01-02 16:00:36.513579	opcional
162	Ausência de caixas de papelão e/ou materiais não adequados?	SIM_NAO_NA	t	t	1	5	t	f	\N	8	2026-01-07 16:34:39.845084	opcional
163	Possui o certificado de coleta e transporte de óleo e gordura vegetal?	SIM_NAO_NA	t	t	1	6	t	f	\N	11	2026-01-08 13:55:23.884516	opcional
164	Presença de Manifesto de Transporte de Resíduos e Rejeitos - MTRR - do mês corrente?	SIM_NAO_NA	t	t	1	8	t	f	\N	11	2026-01-08 13:56:37.036619	opcional
165	A OM possui militar técnico em Nutrição?	SIM_NAO_NA	t	t	1	1	t	f	\N	19	2026-01-08 13:59:40.139823	opcional
166	Caso sim, realiza a elaboração/atualização de fichas técnicas?	SIM_NAO_NA	t	t	1	2	t	f	\N	19	2026-01-08 14:02:17.188437	opcional
167	O refeitório possui sistema de climatização?	SIM_NAO_NA	t	t	1	1	t	f	\N	20	2026-01-08 14:04:26.288602	opcional
168	A temperatura do ambiente é confortável nos horários das refeições?	SIM_NAO_NA	t	t	1	2	t	f	\N	20	2026-01-08 16:06:13.352033	opcional
169	As mesas e cadeiras são confortáveis, bem distribuídas e em quantidade suficiente para a demanda?	SIM_NAO_NA	t	t	1	3	t	f	\N	20	2026-01-08 16:06:41.151358	opcional
170	A iluminação do ambiente é adequada para uma refeição agradável?	SIM_NAO_NA	t	t	1	4	t	f	\N	20	2026-01-08 16:07:05.062965	opcional
171	Há talheres, copos e pratos disponíveis em quantidade adequada à demanda?	SIM_NAO_NA	t	t	1	5	t	f	\N	20	2026-01-08 16:07:21.404376	opcional
172	Os utensílios estão limpos, organizados e em bom estado de conservação (sem rachaduras, etc)?	SIM_NAO_NA	t	t	1	6	t	f	\N	20	2026-01-08 16:07:41.22338	opcional
173	Os equipamentos de distribuição dos alimentos (balcões térmicos, rechauds, cubas) estão em boas condições de uso?	SIM_NAO_NA	t	t	1	7	t	f	\N	20	2026-01-08 16:08:08.843103	opcional
174	Existe reposição eficiente e rápida de utensílios e alimentos durante o serviço?	SIM_NAO_NA	t	t	1	8	t	f	\N	20	2026-01-08 16:08:23.974899	opcional
175	O refeitório apresenta , de forma geral, um ambiente limpo, organizado e bem conservado?	SIM_NAO_NA	t	t	1	9	t	f	\N	20	2026-01-08 16:12:47.470805	opcional
176	A temperatura dos alimentos está adequada, respeitando os padrões de segurança dos alimentos (quente ou fria conforme necessário)?	SIM_NAO_NA	t	t	1	10	t	f	\N	20	2026-01-08 16:13:07.888551	opcional
177	As preparações apresentam boa aparência (cor, textura, disposição e atratividade)?	SIM_NAO_NA	t	t	1	11	t	f	\N	20	2026-01-08 16:13:33.904718	opcional
178	O fluxo de atendimento no refeitório é eficiente, evitando filas e atrasos?	SIM_NAO_NA	t	t	1	12	t	f	\N	20	2026-01-08 16:14:04.63367	opcional
156	TREINAMENTO -  Descrever a temática abordada, metodologia utilizada, % do efetivo participante e as limitações de conhecimento apontadas pelos profissionais do rancho.	TEXTO_LONGO	t	t	0	1	t	f	\N	17	2026-01-02 15:58:05.329792	opcional
157	OBSERVAÇÕES GERAIS E DIFICULDADES ENCONTRADAS PARA A REALIZAÇÃO DO TRABALHO NO MÊS - Apontar se os problemas identificados na primeira visita foram resolvidos ou se persistem e possíveis dificuldades ao realizar as visitas.	TEXTO_LONGO	t	t	0	2	t	f	\N	17	2026-01-02 15:58:11.564085	opcional
\.


--
-- Data for Name: questionario; Type: TABLE DATA; Schema: public; Owner: qualigestor
--

COPY public.questionario (id, nome, descricao, versao, modo, documento_referencia, calcular_nota, ocultar_nota_aplicacao, base_calculo, casas_decimais, modo_configuracao, modo_exibicao_nota, anexar_documentos, capturar_geolocalizacao, restringir_avaliados, habilitar_reincidencia, tipo_preenchimento, pontuacao_ativa, exibir_nota_anterior, exibir_tabela_resumo, exibir_limites_aceitaveis, exibir_data_hora, exibir_questoes_omitidas, exibir_nao_conformidade, cor_relatorio, incluir_assinatura, incluir_foto_capa, agrupamento_fotos, ativo, publicado, status, cliente_id, criado_por_id, criado_em, atualizado_em, data_publicacao) FROM stdin;
1	teste		1	avaliado	\N	f	f	100	2	percentual	PERCENTUAL	f	f	f	f	RAPIDO	t	f	f	f	f	f	f	AZUL	f	f	topico	f	f	INATIVO	2	1	2025-12-17 15:06:52.722165	2026-01-08 13:48:59.980314	2025-12-17 15:07:20.646995
2	Check-List de Monitoramento de Boas Práticas em Segurança Alimentar 2026		1.2	avaliado	\N	t	f	100	2	pontos	PERCENTUAL	t	f	f	f	RAPIDO	t	f	f	f	f	f	f	AZUL	f	f	topico	t	t	PUBLICADO	2	3	2026-01-02 15:20:29.708286	2026-01-08 13:48:59.980319	2026-01-02 16:00:45.778243
3	Teste IA		1	avaliado	\N	t	f	100	2	percentual	PERCENTUAL	t	f	f	f	RAPIDO	t	f	f	f	f	f	f	AZUL	f	f	topico	t	t	PUBLICADO	2	3	2026-01-17 04:28:02.612968	2026-01-17 04:29:42.435147	2026-01-17 04:29:42.433923
\.


--
-- Data for Name: resposta_pergunta; Type: TABLE DATA; Schema: public; Owner: qualigestor
--

COPY public.resposta_pergunta (id, resposta, observacao, pontos, caminho_foto, data_resposta, tempo_resposta, nao_conforme, plano_acao, prazo_plano_acao, responsavel_plano_acao, aplicacao_id, pergunta_id, status_acao, acao_realizada, data_conclusao) FROM stdin;
512	Sim		1	\N	2026-01-22 20:23:11.017623	\N	f	\N	\N	\N	20	5	pendente	\N	\N
353	Porta telada de acesso área externa/setor recebimento não possui dispositivo de fechamento automático. Porta estoque seco sem protetor de rodapé. Embora as caixas de gorduras sejam instaladas nos setores da cozinha, as mesmas se encontram em bom estado de conservação		0	\N	2026-01-19 01:20:02.869152	\N	f	\N	\N	\N	15	22	pendente	\N	\N
472	Sim		1	\N	2026-01-19 01:42:38.485522	\N	f	\N	\N	\N	15	138	pendente	\N	\N
347	Sim		1	\N	2026-01-19 01:19:23.821193	\N	f	\N	\N	\N	15	16	pendente	\N	\N
508	Nenhum		0	\N	2026-01-19 02:18:55.606108	\N	f	\N	\N	\N	15	140	pendente	\N	\N
437	Sim		1	\N	2026-01-19 01:32:32.310696	\N	f	\N	\N	\N	15	105	pendente	\N	\N
430	Coifas apresentando bastante gordura na parte interna.		0	\N	2026-01-19 01:32:01.460286	\N	f	\N	\N	\N	15	98	pendente	\N	\N
431	N.A.		0	\N	2026-01-19 01:32:02.136302	\N	f	\N	\N	\N	15	99	pendente	\N	\N
432	N.A.		0	\N	2026-01-19 01:32:03.247622	\N	f	\N	\N	\N	15	100	pendente	\N	\N
433	N.A.		0	\N	2026-01-19 01:32:04.304352	\N	f	\N	\N	\N	15	101	pendente	\N	\N
434	N.A.		0	\N	2026-01-19 01:32:05.340496	\N	f	\N	\N	\N	15	102	pendente	\N	\N
435	N.A.		0	\N	2026-01-19 01:32:07.210226	\N	f	\N	\N	\N	15	103	pendente	\N	\N
436	Rancho não realiza refeições transportadas		0	\N	2026-01-19 01:32:31.493303	\N	f	\N	\N	\N	15	104	pendente	\N	\N
442	N.A.		0	\N	2026-01-19 01:32:45.409255	\N	f	\N	\N	\N	15	163	pendente	\N	\N
489	N.A.		0	\N	2026-01-19 01:46:20.437532	\N	f	\N	\N	\N	15	177	pendente	\N	\N
351	Não	-	0	resposta_351_c46d23099062.jpg	2026-01-19 01:19:29.976613	\N	t	Instale imediatamente sinalização fotoluminescente das saídas de emergência, incluindo placas indicativas visíveis e rotas de fuga claras, seguido por um treinamento para todos os funcionários sobre a localização e uso das saídas, e realize inspeções semanais para garantir a manutenção e visibilidade da sinalização, documentando cada etapa.	\N	\N	15	20	pendente	\N	\N
335	Não	As portas  estavam em estado muito ruim, o rodapé estva faltando	0	resposta_335_6cb23da3c14b.jpg	2026-01-19 01:18:48.509619	\N	t	Substituir as portas danificadas, garantindo que as novas portas sejam de material de fácil limpeza e de cor clara, e instalar protetor de rodapés em todas as portas substituídas.	\N	\N	15	4	pendente	\N	\N
492	N.A.		0	\N	2026-01-19 01:46:27.711405	\N	f	\N	\N	\N	15	174	pendente	\N	\N
494	N.A.		0	\N	2026-01-19 01:46:30.960719	\N	f	\N	\N	\N	15	172	pendente	\N	\N
443	Sim		1	\N	2026-01-19 01:32:49.826074	\N	f	\N	\N	\N	15	110	pendente	\N	\N
497	N.A.		0	\N	2026-01-19 01:46:34.419926	\N	f	\N	\N	\N	15	169	pendente	\N	\N
444	N.A.		0	\N	2026-01-19 01:36:27.194615	\N	f	\N	\N	\N	15	164	pendente	\N	\N
445	Lixeiras com problema no pedal		0	\N	2026-01-19 01:36:53.431272	\N	f	\N	\N	\N	15	111	pendente	\N	\N
458	Sim		1	\N	2026-01-19 01:41:17.350123	\N	f	\N	\N	\N	15	124	pendente	\N	\N
359	Sim		1	\N	2026-01-19 01:26:25.19593	\N	f	\N	\N	\N	15	28	pendente	\N	\N
439	Sim		1	\N	2026-01-19 01:32:34.451132	\N	f	\N	\N	\N	15	107	pendente	\N	\N
358	Sim		1	\N	2026-01-19 01:26:24.078658	\N	f	\N	\N	\N	15	27	pendente	\N	\N
499	N.A.		0	\N	2026-01-19 01:46:36.862959	\N	f	\N	\N	\N	15	167	pendente	\N	\N
515	Não		0	\N	2026-01-23 17:07:45.855593	\N	f	\N	\N	\N	21	4	pendente	\N	\N
343	Sim		1	\N	2026-01-19 01:19:14.765515	\N	f	\N	\N	\N	15	12	pendente	\N	\N
462	Sim		1	\N	2026-01-19 01:41:26.860999	\N	f	\N	\N	\N	15	128	pendente	\N	\N
346	Sim		1	resposta_346_ffb849837836.jpg	2026-01-19 01:19:22.066848	\N	f	\N	\N	\N	15	15	pendente	\N	\N
438	Sim		1	\N	2026-01-19 01:32:33.34932	\N	f	\N	\N	\N	15	106	pendente	\N	\N
446	Sim		1	\N	2026-01-19 01:40:18.705621	\N	f	\N	\N	\N	15	112	pendente	\N	\N
457	Sim		1	\N	2026-01-19 01:41:14.914378	\N	f	\N	\N	\N	15	123	pendente	\N	\N
477	Sim		1	\N	2026-01-19 01:44:34.763826	\N	f	\N	\N	\N	15	144	pendente	\N	\N
463	Sim		1	\N	2026-01-19 01:41:27.930586	\N	f	\N	\N	\N	15	129	pendente	\N	\N
476	Sim		1	\N	2026-01-19 01:44:33.040556	\N	f	\N	\N	\N	15	143	pendente	\N	\N
483	Sim		1	\N	2026-01-19 01:45:14.208884	\N	f	\N	\N	\N	15	150	pendente	\N	\N
355	Sim		1	\N	2026-01-19 01:26:19.553413	\N	f	\N	\N	\N	15	24	pendente	\N	\N
352	Sim		1	resposta_352_8a9f99abd1d8.jpg	2026-01-19 01:19:46.001857	\N	f	\N	\N	\N	15	21	pendente	\N	\N
354	Sim		1	\N	2026-01-19 01:26:18.548416	\N	f	\N	\N	\N	15	23	pendente	\N	\N
337	Sim		1	resposta_337_9384869f27fb.jpg	2026-01-19 01:18:56.728563	\N	f	\N	\N	\N	15	6	pendente	\N	\N
440	Não	-	0	resposta_440_d5c774525c16.jpg	2026-01-19 01:32:38.943131	\N	t	Instalar tampas com acionamento por pedal em todas as lixeiras internas que não possuam esses dispositivos, garantindo que todas as lixeiras internas estejam em conformidade com o requisito.	\N	\N	15	108	pendente	\N	\N
349	Sim		1	\N	2026-01-19 01:19:26.450012	\N	f	\N	\N	\N	15	18	pendente	\N	\N
348	Sim		1	\N	2026-01-19 01:19:25.039434	\N	f	\N	\N	\N	15	17	pendente	\N	\N
356	Sim		1	\N	2026-01-19 01:26:21.051128	\N	f	\N	\N	\N	15	25	pendente	\N	\N
449	Tela rasgada. Foi solicitado manutenção		0	resposta_449_cf5b76eef718.jpg	2026-01-19 01:40:41.721939	\N	f	\N	\N	\N	15	115	pendente	\N	\N
452	Não	-	0	resposta_452_261396664124.jpg	2026-01-19 01:41:00.866981	\N	t	Implementar imediatamente o registro de monitoramento de temperatura dos alimentos e equipamentos, especificando os parâmetros a serem monitorados, a frequência da medição e o responsável pela execução e registro.	\N	\N	15	118	pendente	\N	\N
361	Sim		1	\N	2026-01-19 01:26:29.041845	\N	f	\N	\N	\N	15	30	pendente	\N	\N
471	Sim		1	\N	2026-01-19 01:42:37.44966	\N	f	\N	\N	\N	15	137	pendente	\N	\N
517	data:image/png;base64,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		0	\N	2026-01-23 20:36:56.142538	\N	f	\N	\N	\N	22	161	pendente	\N	\N
340	Sim		1	\N	2026-01-19 01:19:02.035324	\N	f	\N	\N	\N	15	9	pendente	\N	\N
339	Sim		1	\N	2026-01-19 01:19:00.668176	\N	f	\N	\N	\N	15	8	pendente	\N	\N
357	Sim		1	\N	2026-01-19 01:26:22.553922	\N	f	\N	\N	\N	15	26	pendente	\N	\N
360	Sim		1	\N	2026-01-19 01:26:26.561882	\N	f	\N	\N	\N	15	29	pendente	\N	\N
467	Controle de temperatura não estão sendo controlados		0	\N	2026-01-19 01:41:57.166363	\N	f	\N	\N	\N	15	133	pendente	\N	\N
350	Sim		1	\N	2026-01-19 01:19:28.860714	\N	f	\N	\N	\N	15	19	pendente	\N	\N
336	Sim		1	resposta_336_b9622573ed1b.jpg	2026-01-19 01:18:54.898531	\N	f	\N	\N	\N	15	5	pendente	\N	\N
503	Persiste problemas nos pedais de acionamento …..		0	\N	2026-01-19 01:48:08.568988	\N	f	\N	\N	\N	15	157	pendente	\N	\N
505	Ten Nut Alcântara		0	\N	2026-01-19 01:48:42.078148	\N	f	\N	\N	\N	15	158	pendente	\N	\N
342	Sim		1	resposta_342_3b73b0f5d1ae.jpg	2026-01-19 01:19:13.456919	\N	f	\N	\N	\N	15	11	pendente	\N	\N
338	Sim		1	\N	2026-01-19 01:18:59.288443	\N	f	\N	\N	\N	15	7	pendente	\N	\N
366	Limpeza do ambiente realizada por empresa terceirizada		0	\N	2026-01-19 01:27:16.107087	\N	f	\N	\N	\N	15	35	pendente	\N	\N
393	Nenhum óbice		0	\N	2026-01-19 01:29:58.153869	\N	f	\N	\N	\N	15	62	pendente	\N	\N
330	Sim		1	resposta_330_e52e60a8a817.png	2026-01-17 04:33:42.669446	\N	f	\N	\N	\N	10	179	pendente	\N	\N
419	Nenhum óbice		0	\N	2026-01-19 01:31:13.97562	\N	f	\N	\N	\N	15	87	pendente	\N	\N
410	N.A.		0	\N	2026-01-19 01:30:34.641429	\N	f	\N	\N	\N	15	162	pendente	\N	\N
447	Não	-	0	resposta_447_ba178613094d.jpg	2026-01-19 01:40:19.425453	\N	t	Substituir a tela rasgada identificada, vedar os ralos abertos e remover o lixo exposto da área, assegurando a eliminação imediata dos pontos de não conformidade.	\N	\N	15	113	pendente	\N	\N
469	Sim		1	\N	2026-01-19 01:42:34.637838	\N	f	\N	\N	\N	15	135	pendente	\N	\N
506	data:image/png;base64,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		0	\N	2026-01-19 01:48:47.085865	\N	f	\N	\N	\N	15	161	pendente	\N	\N
486	Sim		1	\N	2026-01-19 01:45:27.05872	\N	f	\N	\N	\N	15	153	pendente	\N	\N
406	Sim		1	\N	2026-01-19 01:30:28.964644	\N	f	\N	\N	\N	15	75	pendente	\N	\N
453	Não	-	0	resposta_453_fd73742293c8.jpg	2026-01-19 01:41:01.834926	\N	t	Implementar imediatamente um sistema de registro de monitoramento da higienização de todos os ambientes, contendo data, horário, responsável e assinatura, bem como os parâmetros de avaliação da limpeza, para assegurar a conformidade com os procedimentos de higiene estabelecidos.	\N	\N	15	119	pendente	\N	\N
464	Sim		1	\N	2026-01-19 01:41:29.806799	\N	f	\N	\N	\N	15	130	pendente	\N	\N
411	Sim		1	\N	2026-01-19 01:30:36.725968	\N	f	\N	\N	\N	15	79	pendente	\N	\N
513	Sim		1	\N	2026-01-22 20:23:12.971584	\N	f	\N	\N	\N	20	6	pendente	\N	\N
417	Sim		1	\N	2026-01-19 01:30:43.43563	\N	f	\N	\N	\N	15	85	pendente	\N	\N
465	Sim		1	\N	2026-01-19 01:41:30.915751	\N	f	\N	\N	\N	15	131	pendente	\N	\N
474	Sim		1	\N	2026-01-19 01:44:30.557273	\N	f	\N	\N	\N	15	141	pendente	\N	\N
331	Não	Acordou e foi direto para o  celular, perdendo o foco de concluir a tarefa de arrumação da cama ao acordar	0	resposta_331_56b50a04db4a.jpg	2026-01-17 04:34:31.19223	\N	t	Estabeleça um alarme com lembrete sonoro e visual específico para "Arrumar a cama" imediatamente após desligar o primeiro alarme matinal; coloque o celular em outro cômodo ou dentro de uma gaveta longe do alcance visual e auditivo ao despertar, impedindo o acesso imediato e forçando a priorização da arrumação da cama; após concluir a tarefa, recompense-se com 5 minutos de uso do celular como incentivo ao cumprimento da rotina estabelecida.	\N	\N	10	180	pendente	\N	\N
416	Sim		1	\N	2026-01-19 01:30:42.2037	\N	f	\N	\N	\N	15	84	pendente	\N	\N
344	Sim		1	\N	2026-01-19 01:19:16.839279	\N	f	\N	\N	\N	15	13	pendente	\N	\N
385	Sim		1	\N	2026-01-19 01:29:33.471053	\N	f	\N	\N	\N	15	54	pendente	\N	\N
409	Sim		1	\N	2026-01-19 01:30:33.658861	\N	f	\N	\N	\N	15	78	pendente	\N	\N
364	Sim		1	\N	2026-01-19 01:26:38.172076	\N	f	\N	\N	\N	15	33	pendente	\N	\N
382	Sim		1	\N	2026-01-19 01:29:28.90257	\N	f	\N	\N	\N	15	51	pendente	\N	\N
481	N.A.		0	\N	2026-01-19 01:45:10.341194	\N	f	\N	\N	\N	15	148	pendente	\N	\N
413	Sim		1	\N	2026-01-19 01:30:38.813993	\N	f	\N	\N	\N	15	81	pendente	\N	\N
478	Sim		1	\N	2026-01-19 01:44:36.427053	\N	f	\N	\N	\N	15	145	pendente	\N	\N
487	Nenhum		0	\N	2026-01-19 01:46:17.007807	\N	f	\N	\N	\N	15	154	pendente	\N	\N
488	N.A.		0	\N	2026-01-19 01:46:19.387784	\N	f	\N	\N	\N	15	178	pendente	\N	\N
491	N.A.		0	\N	2026-01-19 01:46:23.452503	\N	f	\N	\N	\N	15	175	pendente	\N	\N
388	Sim		1	\N	2026-01-19 01:29:36.790483	\N	f	\N	\N	\N	15	57	pendente	\N	\N
493	N.A.		0	\N	2026-01-19 01:46:29.799395	\N	f	\N	\N	\N	15	173	pendente	\N	\N
363	Sim		1	\N	2026-01-19 01:26:35.755529	\N	f	\N	\N	\N	15	32	pendente	\N	\N
333	Não		0	\N	2026-01-17 23:46:53.111772	\N	f	\N	\N	\N	13	179	pendente	\N	\N
496	N.A.		0	\N	2026-01-19 01:46:33.234133	\N	f	\N	\N	\N	15	170	pendente	\N	\N
332	Sim		1	\N	2026-01-17 04:37:37.992988	\N	f	\N	\N	\N	10	181	pendente	\N	\N
450	Sim		1	\N	2026-01-19 01:40:58.586736	\N	f	\N	\N	\N	15	116	pendente	\N	\N
362	Sim		1	\N	2026-01-19 01:26:34.31262	\N	f	\N	\N	\N	15	31	pendente	\N	\N
498	N.A.		0	\N	2026-01-19 01:46:35.618753	\N	f	\N	\N	\N	15	168	pendente	\N	\N
501	N.A.		0	\N	2026-01-19 01:46:41.345244	\N	f	\N	\N	\N	15	166	pendente	\N	\N
415	Sim		1	\N	2026-01-19 01:30:40.899886	\N	f	\N	\N	\N	15	83	pendente	\N	\N
365	Sim		1	\N	2026-01-19 01:26:39.281422	\N	f	\N	\N	\N	15	34	pendente	\N	\N
418	Sim		1	\N	2026-01-19 01:30:44.48578	\N	f	\N	\N	\N	15	86	pendente	\N	\N
384	Sim		1	\N	2026-01-19 01:29:32.316223	\N	f	\N	\N	\N	15	53	pendente	\N	\N
468	Sim		1	\N	2026-01-19 01:42:33.84782	\N	f	\N	\N	\N	15	134	pendente	\N	\N
386	Sim		1	\N	2026-01-19 01:29:34.597553	\N	f	\N	\N	\N	15	55	pendente	\N	\N
391	Sim		1	\N	2026-01-19 01:29:40.041092	\N	f	\N	\N	\N	15	60	pendente	\N	\N
518	Sim		1	\N	2026-01-24 13:22:42.850261	\N	f	\N	\N	\N	24	179	pendente	\N	\N
345	Não	-	0	resposta_345_f1982e0b56b6.jpg	2026-01-19 01:19:18.121222	\N	t	jdsafghdas	\N	\N	15	14	pendente	\N	\N
455	Sim		1	\N	2026-01-19 01:41:12.464985	\N	f	\N	\N	\N	15	121	pendente	\N	\N
383	Sim		1	\N	2026-01-19 01:29:30.058143	\N	f	\N	\N	\N	15	52	pendente	\N	\N
389	Sim		1	\N	2026-01-19 01:29:37.959331	\N	f	\N	\N	\N	15	58	pendente	\N	\N
387	Sim		1	\N	2026-01-19 01:29:35.72916	\N	f	\N	\N	\N	15	56	pendente	\N	\N
479	Sim		1	\N	2026-01-19 01:44:41.359951	\N	f	\N	\N	\N	15	146	pendente	\N	\N
390	Sim		1	\N	2026-01-19 01:29:39.066153	\N	f	\N	\N	\N	15	59	pendente	\N	\N
421	Sim		1	\N	2026-01-19 01:31:15.824875	\N	f	\N	\N	\N	15	88	pendente	\N	\N
420	Não	-	0	resposta_420_9aecb26c6c2c.jpg	2026-01-19 01:31:13.994035	\N	t	Considerando que a observação do auditor foi vazia ("-"), presumo que o auditor encontrou um ou mais equipamentos que necessitam de limpeza orgânica (por meio de contratação de serviço) e que não estavam em boas condições de uso. Portanto, a ação corretiva deve ser direcionada a consertar ou substituir esses equipamentos específicos. Consertar/Substituir os equipamentos identificados durante a auditoria que necessitam de limpeza orgânica e que não se encontram em boas condições de uso, assegurando que estejam em pleno funcionamento e aptos para o processo de limpeza contratado.	\N	\N	15	89	pendente	\N	\N
459	Sim		1	\N	2026-01-19 01:41:18.766233	\N	f	\N	\N	\N	15	125	pendente	\N	\N
392	Sim		1	\N	2026-01-19 01:29:41.187319	\N	f	\N	\N	\N	15	61	pendente	\N	\N
414	Sim		1	\N	2026-01-19 01:30:39.821622	\N	f	\N	\N	\N	15	82	pendente	\N	\N
412	Sim		1	\N	2026-01-19 01:30:37.746625	\N	f	\N	\N	\N	15	80	pendente	\N	\N
473	Sim		1	\N	2026-01-19 01:42:39.480144	\N	f	\N	\N	\N	15	139	pendente	\N	\N
482	Sim		1	\N	2026-01-19 01:45:12.982885	\N	f	\N	\N	\N	15	149	pendente	\N	\N
519	Sim		1	\N	2026-01-24 13:22:43.270219	\N	f	\N	\N	\N	24	181	pendente	\N	\N
334	data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAASwAAACWCAYAAABkW7XSAAAAAXNSR0IArs4c6QAAAERlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAA6ABAAMAAAABAAEAAKACAAQAAAABAAABLKADAAQAAAABAAAAlgAAAABJS0H3AAADlUlEQVR4Ae3XMQoCQRAEwFNTEfQVgomJ+ANDX21iaORLjM/dvB/QQR1c0ps0NTAwy+IjQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIAsdtCEUECBBoFLhaWI1j0YkAgSTwSKGMAAECjQLvxlI6ESBAIAmsTsLEIiNAoFLAwqoci1IECCQBCyupyAgQaBM4zEIWVttY9CFAIAlcZmhhJRoZAQJtAvdZaNfWSh8CBAgEgefIfpvwICJAgECbwHcUejkJ28aiDwECSeA8wk96kBEgQKBJYF6C6/hvTaV0IUCAQBI4jXAurP0f3icI/VVhtvAAAAAASUVORK5CYII=		0	\N	2026-01-18 17:10:18.344986	\N	f	\N	\N	\N	12	161	pendente	\N	\N
367	N.A.		0	\N	2026-01-19 01:27:20.335686	\N	f	\N	\N	\N	15	36	pendente	\N	\N
372	N.A.		0	\N	2026-01-19 01:27:33.89473	\N	f	\N	\N	\N	15	41	pendente	\N	\N
373	N.A.		0	\N	2026-01-19 01:27:35.111439	\N	f	\N	\N	\N	15	42	pendente	\N	\N
374	N.A.		0	\N	2026-01-19 01:27:36.719275	\N	f	\N	\N	\N	15	43	pendente	\N	\N
379	N.A.		0	\N	2026-01-19 01:28:01.447133	\N	f	\N	\N	\N	15	48	pendente	\N	\N
381	Rancho com meio de expediente não havendo produção. Somente ocorrendo café da manhã		0	\N	2026-01-19 01:28:41.327555	\N	f	\N	\N	\N	15	50	pendente	\N	\N
405	Nenhum óbice		0	\N	2026-01-19 01:30:26.798937	\N	f	\N	\N	\N	15	74	pendente	\N	\N
502	Tema: higiene ambiental ……		0	\N	2026-01-19 01:47:45.489519	\N	f	\N	\N	\N	15	156	pendente	\N	\N
504	data:image/png;base64,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		0	\N	2026-01-19 01:48:37.162394	\N	f	\N	\N	\N	15	159	pendente	\N	\N
480	Nenhum óbice		0	\N	2026-01-19 01:44:55.666562	\N	f	\N	\N	\N	15	147	pendente	\N	\N
490	N.A.		0	\N	2026-01-19 01:46:21.591603	\N	f	\N	\N	\N	15	176	pendente	\N	\N
495	N.A.		0	\N	2026-01-19 01:46:32.146217	\N	f	\N	\N	\N	15	171	pendente	\N	\N
441	Não	-	0	resposta_441_e9e0d1ee3b21.jpg	2026-01-19 01:32:39.960242	\N	t	Remover imediatamente o resíduo orgânico da área refrigerada, destinando-o ao local apropriado para descarte, conforme procedimento de gerenciamento de resíduos.	\N	\N	15	109	pendente	\N	\N
500	N.A.		0	\N	2026-01-19 01:46:40.175841	\N	f	\N	\N	\N	15	165	pendente	\N	\N
507	Monica Lobo		0	\N	2026-01-19 01:48:48.955099	\N	f	\N	\N	\N	15	160	pendente	\N	\N
425	Sim		1	\N	2026-01-19 01:31:24.548185	\N	f	\N	\N	\N	15	93	pendente	\N	\N
454	Não	-	0	resposta_454_2aa783334208.jpg	2026-01-19 01:41:02.862165	\N	t	Implementar imediatamente um sistema de registro de monitoramento da higienização de equipamentos, contendo data, horário, responsável e os parâmetros avaliados durante a higienização de cada equipamento.	\N	\N	15	120	pendente	\N	\N
404	Sim		1	\N	2026-01-19 01:30:13.249745	\N	f	\N	\N	\N	15	73	pendente	\N	\N
403	Sim		1	\N	2026-01-19 01:30:12.233321	\N	f	\N	\N	\N	15	72	pendente	\N	\N
429	Sim		1	\N	2026-01-19 01:31:30.519017	\N	f	\N	\N	\N	15	97	pendente	\N	\N
448	Sim		1	\N	2026-01-19 01:40:21.223667	\N	f	\N	\N	\N	15	114	pendente	\N	\N
516			0	\N	2026-01-23 20:36:45.851169	\N	f	\N	\N	\N	22	159	pendente	\N	\N
398	Sim		1	\N	2026-01-19 01:30:06.39688	\N	f	\N	\N	\N	15	67	pendente	\N	\N
511	Não	não tinha pallet.	0	\N	2026-01-22 20:22:03.835411	\N	f	\N	\N	\N	20	4	pendente	\N	\N
514	Sim		1	\N	2026-01-22 20:23:14.627113	\N	f	\N	\N	\N	20	7	pendente	\N	\N
378	Sim		1	\N	2026-01-19 01:28:00.149398	\N	f	\N	\N	\N	15	47	pendente	\N	\N
423	Sim		1	\N	2026-01-19 01:31:22.073629	\N	f	\N	\N	\N	15	91	pendente	\N	\N
451	Sim		1	\N	2026-01-19 01:40:59.498449	\N	f	\N	\N	\N	15	117	pendente	\N	\N
377	Sim		1	\N	2026-01-19 01:27:55.891572	\N	f	\N	\N	\N	15	46	pendente	\N	\N
427	Sim		1	\N	2026-01-19 01:31:26.545452	\N	f	\N	\N	\N	15	95	pendente	\N	\N
397	Sim		1	\N	2026-01-19 01:30:05.096615	\N	f	\N	\N	\N	15	66	pendente	\N	\N
461	Sim		1	\N	2026-01-19 01:41:25.784826	\N	f	\N	\N	\N	15	127	pendente	\N	\N
396	Sim		1	\N	2026-01-19 01:30:03.269447	\N	f	\N	\N	\N	15	65	pendente	\N	\N
375	Não	-	0	resposta_375_c55449b9dac9.jpg	2026-01-19 01:27:39.87859	\N	t	Realocar imediatamente as caixas de gordura para uma área apropriada, distante da produção de alimentos, ou implementar barreiras físicas eficazes que previnam qualquer risco de contaminação, seguido de uma revisão do layout da planta e treinamento da equipe sobre as novas normas de segurança alimentar para garantir a conformidade contínua.	\N	\N	15	44	pendente	\N	\N
456	Sim		1	\N	2026-01-19 01:41:13.725692	\N	f	\N	\N	\N	15	122	pendente	\N	\N
376	Sim		1	\N	2026-01-19 01:27:48.012949	\N	f	\N	\N	\N	15	45	pendente	\N	\N
470	Sim		1	\N	2026-01-19 01:42:36.337153	\N	f	\N	\N	\N	15	136	pendente	\N	\N
380	Sim		1	\N	2026-01-19 01:28:08.877308	\N	f	\N	\N	\N	15	49	pendente	\N	\N
394	Sim		1	\N	2026-01-19 01:30:00.984408	\N	f	\N	\N	\N	15	63	pendente	\N	\N
402	Sim		1	\N	2026-01-19 01:30:11.112048	\N	f	\N	\N	\N	15	71	pendente	\N	\N
399	Sim		1	\N	2026-01-19 01:30:07.423769	\N	f	\N	\N	\N	15	68	pendente	\N	\N
475	Sim		1	\N	2026-01-19 01:44:31.449399	\N	f	\N	\N	\N	15	142	pendente	\N	\N
484	Sim		1	\N	2026-01-19 01:45:18.303305	\N	f	\N	\N	\N	15	151	pendente	\N	\N
368	Sim		1	\N	2026-01-19 01:27:24.697095	\N	f	\N	\N	\N	15	37	pendente	\N	\N
422	Sim		1	\N	2026-01-19 01:31:17.668348	\N	f	\N	\N	\N	15	90	pendente	\N	\N
424	Sim		1	\N	2026-01-19 01:31:24.273626	\N	f	\N	\N	\N	15	92	pendente	\N	\N
369	Sim		1	\N	2026-01-19 01:27:25.780522	\N	f	\N	\N	\N	15	38	pendente	\N	\N
426	Sim		1	\N	2026-01-19 01:31:25.655511	\N	f	\N	\N	\N	15	94	pendente	\N	\N
428	Sim		1	\N	2026-01-19 01:31:27.532631	\N	f	\N	\N	\N	15	96	pendente	\N	\N
370	Sim		1	\N	2026-01-19 01:27:28.398757	\N	f	\N	\N	\N	15	39	pendente	\N	\N
371	Sim		1	\N	2026-01-19 01:27:29.891829	\N	f	\N	\N	\N	15	40	pendente	\N	\N
395	Sim		1	\N	2026-01-19 01:30:01.767332	\N	f	\N	\N	\N	15	64	pendente	\N	\N
341	Não	Tela da janela estava rasgada	0	resposta_341_a9ca5d255389.jpg	2026-01-19 01:19:08.100119	\N	t	ou substituir imediatamente a tela rasgada da janela, assegurando que a malha esteja íntegra e sem aberturas, restabelecendo a barreira física contra a entrada de pragas e vetores.	\N	\N	15	10	pendente	\N	\N
401	Sim		1	\N	2026-01-19 01:30:09.477644	\N	f	\N	\N	\N	15	70	pendente	\N	\N
400	Sim		1	\N	2026-01-19 01:30:08.414721	\N	f	\N	\N	\N	15	69	pendente	\N	\N
460	Não	-	0	resposta_460_41566c73f039.jpg	2026-01-19 01:41:19.950101	\N	t	Elaborar e implementar imediatamente um plano de calibração para todos os termômetros de medição utilizados, incluindo a identificação dos mesmos, frequência de calibração, método de calibração e responsável pela execução, registrando os resultados em planilha específica.	\N	\N	15	126	pendente	\N	\N
466	Não	-	0	resposta_466_91be2f1fbd6c.jpg	2026-01-19 01:41:32.294681	\N	t	Elaborar e implementar imediatamente um registro padronizado para documentar todos os casos suspeitos de Doença Transmitida por Alimentos (DTA), contendo data, identificação do indivíduo, sintomas relatados, alimentos suspeitos e ações tomadas.	\N	\N	15	132	pendente	\N	\N
407	Sim		1	\N	2026-01-19 01:30:30.576786	\N	f	\N	\N	\N	15	76	pendente	\N	\N
408	Sim		1	\N	2026-01-19 01:30:31.66348	\N	f	\N	\N	\N	15	77	pendente	\N	\N
485	Não	-	0	resposta_485_b6e2b102862f.jpg	2026-01-19 01:45:24.242236	\N	t	Elaborar e implementar, em até 30 dias, um plano de ação com atividades específicas de promoção da saúde e prevenção de doenças, direcionado ao efetivo da OM, incluindo temas relevantes e cronograma de execução, com posterior registro das ações realizadas.	\N	\N	15	152	pendente	\N	\N
520	Não	Levantou e foi direto para o sofá, não retornou para arrumar a cama na parte da manhã	0	resposta_520_3962fc9d59ae.jpg	2026-01-24 13:22:43.55624	\N	f	\N	\N	\N	24	180	pendente	\N	\N
\.


--
-- Data for Name: topico; Type: TABLE DATA; Schema: public; Owner: qualigestor
--

COPY public.topico (id, nome, descricao, ordem, ativo, questionario_id, categoria_indicador_id) FROM stdin;
1	teste		1	t	1	\N
21	Rotina ao Acordar em cas		1	t	3	\N
2	Abertura		1	f	2	\N
5	Higiene e Segurança dos Alimentos		3	t	2	\N
6	Higiene Ambiental		4	t	2	\N
7	Armazenagem - Estoque Seco		5	t	2	\N
8	Armazenagem - Estoque frio		6	t	2	\N
9	Utensílios, Equipamentos e Mobiliário		7	t	2	\N
10	Refeição transportada		8	t	2	\N
11	Lixo e Área de Descarte		9	t	2	\N
12	Controle de Pragas e Vetores		10	t	2	\N
13	Registros		11	t	2	\N
14	Análises Microbiológicas		12	t	2	\N
15	Vestiários		13	t	2	\N
16	Qualidade dos cardápios de acordo com a ICA 145-16		14	t	2	\N
19	Efetivo do Rancho		15	t	2	\N
20	Ambiente e conforto - Refeitórios		16	t	2	\N
17	Conclusão		17	t	2	\N
18	Assinaturas		18	t	2	\N
3	Infraestrutura		1	t	2	\N
4	Higiene e Segurança Pessoal		2	t	2	\N
22	teste		19	t	2	\N
\.


--
-- Data for Name: usuario; Type: TABLE DATA; Schema: public; Owner: qualigestor
--

COPY public.usuario (id, nome, email, senha_hash, telefone, tipo, ativo, ultimo_acesso, cliente_id, grupo_id, avaliado_id, criado_em) FROM stdin;
1	Administrador	admin@admin.com	pbkdf2:sha256:600000$KAUagNCgYsGMAVYs$155423a3f7a647fa39aee93c0c35b8e7a845e91bf98fc33c3edca36509734f24	\N	ADMIN	t	\N	2	\N	\N	2025-12-17 15:06:12.47211
25	Andrea Flores Oliveira	andreaflores.nutri@gmail.com	pbkdf2:sha256:600000$ox0I2QaYcierG5YQ$f770246f12d254550627f0cc22b27647145a0425782a3031ed98b795e31e3787	\N	AUDITOR	t	\N	2	74	\N	2026-01-23 19:41:07.401466
26	Pâmela Esmeralda	nutripamelaesmeralda@outlook.com	pbkdf2:sha256:600000$BpE3Y32gwYiy4q3e$4441d850a45f934717dee101a3107ebc5dafab416c88d24530ab426cf5235654	\N	AUDITOR	t	\N	2	75	\N	2026-01-23 19:41:29.337768
27	Karla Andréa Costa Cunto	karlacnt@gmail.com	pbkdf2:sha256:600000$Jq1AqfGyqrFms0FP$bd5bf79642743f2adaecbbbd7e3c5f666524dc0c62b8c0158fba5f741dc288c3	\N	AUDITOR	t	\N	2	63	\N	2026-01-23 19:42:00.954459
7	PAME-RJ	pamerj@labmattos.com.br	pbkdf2:sha256:600000$FBiPs4UBzaf1RNpB$ddd0e0d46624c1eafada90b496302766f23121c72e211748a65ef7508b056c7a	\N	USUARIO	t	\N	2	56	95	2026-01-09 00:45:20.609847
3	José Victor	ti@labmattos.com.br	pbkdf2:sha256:600000$q2EzQsCzRZmj9WAg$1fe63a0c211a4affbc51456ee64f8c868cc614bdde5ddf9081f53349e04f6f9c	\N	SUPER_ADMIN	t	\N	2	\N	\N	2025-12-19 13:20:43.786811
8	Teste Gestor	gestor@teste.com	pbkdf2:sha256:600000$MUu4qzPW7X8nD7Av$cf556c2ce8e0a10b52cd0cace69563b1ed484ca07e5e89a64c13889eed2791f5	\N	GESTOR	t	\N	2	58	\N	2026-01-19 00:04:33.010123
9	Teste Rancho	rancho@teste.com	pbkdf2:sha256:600000$VSr7ucMJa2LcCXsB$d31c9449eadc0fbdcb757cb8862c834dd1505bdf000cba52d408702b7b2a2f7b	\N	USUARIO	t	\N	2	58	104	2026-01-19 00:05:17.837777
28	Danielle Morato da Silva	nutridaniellem@gmail.com	pbkdf2:sha256:600000$iLgUpIIVhlyOO4z0$e4d53d3d4df7ea312197e7f384119d8bfb627c10b415fd0a059f075c254a4095	\N	AUDITOR	t	\N	2	64	\N	2026-01-23 19:42:29.872153
2	Jéssica	aeronautica@labmattos.com.br	pbkdf2:sha256:600000$vR9POPNLHIKWgfZ8$31be24ef60a3a973a3dc1a398e61272071a6356d30b534f249867488567c37d5	\N	ADMIN	t	\N	2	\N	\N	2025-12-18 16:05:26.179183
11	Luiza Marcelle	nutriluizajacob@gmail.com	pbkdf2:sha256:600000$C90QaY2V3n4WDzB7$6113583263b1fc3a36beec8b59358d135f0e14af8714db7fe311bc2a1ed23454	\N	AUDITOR	t	\N	2	56	\N	2026-01-23 19:23:56.318226
12	Dandara Santanna Laut	dandaralaut@gmail.com	pbkdf2:sha256:600000$HYr5VDpy8pzHf2ya$cd9d404c713d07cb74ab83a25e6c988462053f7000ced6c9cac907a67b3c4825	\N	AUDITOR	t	\N	2	57	\N	2026-01-23 19:25:37.336153
13	Ana Claudia  Lourenço Magalhães	anaclaudianutri35@gmail.com	pbkdf2:sha256:600000$ofKk1eoxsLuZZeZY$24399c8f9628f42faf9861fdfb4607325a443313ab2d45feefeb36cb18f70852	\N	AUDITOR	t	\N	2	58	\N	2026-01-23 19:30:31.715848
17	Maria Cristina  Almeida Pinto	mcris.almeida@hotmail.com	pbkdf2:sha256:600000$cWTabNqwEOOG1Pff$9dd8293c3d755005fc64a1d88ad43a7323a25ab01482b10711cdc44856b45f76	\N	AUDITOR	t	\N	2	59	\N	2026-01-23 19:33:18.049559
10	Consultor	teste@consultora.com	pbkdf2:sha256:600000$wWDRQCb5zJmgqKk3$cb748a2b27241d7d4c67effc0edb90b895ff42cb164f5891525137429dec3575	\N	AUDITOR	t	\N	2	69	\N	2026-01-19 00:50:59.353954
19	Mariana Ferreira da Silva	smarianaferreiras@gmail.com	pbkdf2:sha256:600000$o9Y0VdG6HWzoKoiH$a85587615d2792fcf2c6eef60bfc02c74791d02e64b1cb30e72d88fb7ecf4469	\N	AUDITOR	t	\N	2	60	\N	2026-01-23 19:35:22.744292
20	Deisiane Franciele  da Silva Costa	nutri.deisianefr@gmail.com	pbkdf2:sha256:600000$LcIgKorNIRvQiIzG$b07e5887d434fa3570def522ec3437dc51a0429eda6462b630ae654b70cedb4c	\N	AUDITOR	t	\N	2	71	\N	2026-01-23 19:36:03.369887
21	Mirlene Sena Costa	mirlene.costa21@hotmail.com	pbkdf2:sha256:600000$Nc9IzH2yzxYGGqae$f4017611256bc7392e54c52737fe0d9c3f70a3dd527809ec35e52c7254315a7d	\N	AUDITOR	t	\N	2	61	\N	2026-01-23 19:37:41.654484
6	teste Rejane	rejane@teste.com	pbkdf2:sha256:600000$eFfhSbSB6GBGOugi$677a06d8ba055d2454c3d320331e9bbc26c5e246368a261403cb069dac52b62a	\N	AUDITOR	t	\N	2	62	\N	2026-01-08 21:25:44.722324
31	Rebeka	dpaulacolares01@gmail.com	pbkdf2:sha256:600000$oQSTGoh1j60f1boW$2278a8c715a9ba40fb7b54d5d7a5d77f0e681094223d42b06ff09586ff33de09	\N	AUDITOR	t	\N	2	78	\N	2026-01-23 19:44:14.623805
33	Kleidione Teixeira  de Moura	kleidione@yahoo.com.br	pbkdf2:sha256:600000$ZpG5k3Q6Rh0wIRZm$5939c817229a1d3e4e35a93edee3296b7c6dfebf33700e5e7586b428d2cc3872	\N	AUDITOR	t	\N	2	80	\N	2026-01-23 19:45:02.362163
34	Laís Adalgiza  Vieira de Souza	nutrilaisvieira@gmail.com	pbkdf2:sha256:600000$SXIRlYbzRAte68ww$2afc37c2931bce9c634cc48788ade86426d765bf8055c6baef22c9a6b4410e9e	\N	AUDITOR	t	\N	2	65	\N	2026-01-23 19:45:22.176268
35	Iasmine Vasconcelos  Villa	consultoria.iasminevilla@hotmail.com	pbkdf2:sha256:600000$Vbok98KsT98NQn3z$9550776f1960e3a90df087df26139da1d8480aa800c78577f6dbed94cdc23aae	\N	AUDITOR	t	\N	2	83	\N	2026-01-23 19:45:43.706852
37	Samara Cristina  Pereira curado	sammaranutri@gmail.com	pbkdf2:sha256:600000$qj3ktZ3X8tSuEvhl$70479bcc3c768033c3b9218f39961d99d1f801fc111fb69f6ab906055722841c	\N	AUDITOR	t	\N	2	84	\N	2026-01-23 19:47:30.495691
38	Dila Fernandes  Barreto Sampaio	dilanut@hotmail.com	pbkdf2:sha256:600000$YlAwn3ca6WzAc1Na$967167bfa2337ae91e7fbf2a70762a12361a98d3835ff339c3dcf94cc55b2493	\N	AUDITOR	t	\N	2	67	\N	2026-01-23 19:47:52.866977
32	Alcione Maria  Moreira de Oliveira 	alcione.doc.geral@gmail.com	pbkdf2:sha256:600000$LdKo8MpMFDYGjRo5$f26d6af1707f269e7b92b503ca85a8bfc631308cc756eabbffcc2afb00e1f976	\N	AUDITOR	t	\N	2	79	\N	2026-01-23 19:44:32.239046
24	Larissa Menezes Pacheco	nutricao.larissampacheco@gmail.com	pbkdf2:sha256:600000$aUbMdSSe5v0cAMXn$4db4f65d0ec71263b01865e5efaa3f97d772df7fbdcee854038414cda589bb9e	\N	AUDITOR	t	\N	2	62	\N	2026-01-23 19:40:39.965653
14	Paula Ferreira  Rita da Silva	paularita.nutricionista@gmail.com	pbkdf2:sha256:600000$A0zJdy7CTGltsp8m$cd19209498e42bd523b4634e24712bf90047f51501c8df06cb31c4b6250434cf	\N	AUDITOR	t	\N	2	68	\N	2026-01-23 19:31:13.018922
23	Rejane Cerqueira	rejane.fontoura@yahoo.com.br	pbkdf2:sha256:600000$hXs47NqXiMEe4YUs$b0831daf98fe3a8fc4f03172ec7ba6c0a54189f26873e99a5ea9634c25948bd4	\N	AUDITOR	t	\N	2	62	\N	2026-01-23 19:39:48.122563
30	Augiceli Barbosa  De Oliveira Rodrigues	augicelibarbosade@gmail.com	pbkdf2:sha256:600000$lpzhfzvIYXsnYZEp$ff4b5f43439e848057f145e32520a2733d9e5d57d3f2aa3b9cb5a8614628df9a	\N	AUDITOR	t	\N	2	77	\N	2026-01-23 19:43:31.674167
29	Vivian Lima Nascimento	vivian_ln04@hotmail.com	pbkdf2:sha256:600000$fa7JSRUr12hAmzoN$068ad947bdcfc6b6f444f6a154aa1d46abdf8a41411470d5d84df365b5dbba7c	\N	AUDITOR	t	\N	2	76	\N	2026-01-23 19:42:47.087306
15	Fernanda Cristina  Biagiotti de Souza	ferbiagiotticorrea@gmail.com	pbkdf2:sha256:600000$JptKKmMqk1f2vh5n$92dd4627821986008e8c1f01f45786d88b1ca67e294851854a33fb2061912b76	\N	AUDITOR	t	\N	2	59	\N	2026-01-23 19:32:22.295225
18	Monica Queiroz Lobo	monica.q.l@hotmail.com	pbkdf2:sha256:600000$KoClbSmFfQycrd7F$f9862433f58dc13438e500bd3faf44e4e2feade67f03a2e654cea1ded370393d	\N	AUDITOR	t	\N	2	69	\N	2026-01-23 19:34:56.450783
22	Camila Serro Vargas	camilaserrovargas@hotmail.com	pbkdf2:sha256:600000$qB3HpdTSS1Rvezqi$88c516f569b0b47450023a94650e9304647956234ebfbc7dd820e320cf220375	\N	AUDITOR	t	\N	2	73	\N	2026-01-23 19:38:01.215776
16	Elisabete Carrieri	betecese@gmail.com	pbkdf2:sha256:600000$RYWoAlmefrJzksmE$30047ac1ac1d4288b94a67f1a952b276380f8637ec1465bd5c0f2a87c3a217e6	\N	AUDITOR	t	\N	2	59	\N	2026-01-23 19:32:45.037661
36	Débora Lovisi  Silva Gomide	dgomide@gmail.com	pbkdf2:sha256:600000$ruaEivkP7HR1G5Mn$ee33669cddc39ff9e74b51993677f460616e58a2bdeee78ca341002164694eb4	\N	AUDITOR	t	\N	2	66	\N	2026-01-23 19:46:59.450064
\.


--
-- Data for Name: usuario_autorizado; Type: TABLE DATA; Schema: public; Owner: qualigestor
--

COPY public.usuario_autorizado (id, questionario_id, usuario_id, criado_em) FROM stdin;
1	1	1	2025-12-17 15:06:52.726833
2	2	1	2026-01-02 15:20:29.783902
3	2	3	2026-01-02 15:20:29.783906
4	2	2	2026-01-02 15:20:29.783908
5	3	3	2026-01-17 04:28:02.636963
\.


--
-- Name: aplicacao_questionario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qualigestor
--

SELECT pg_catalog.setval('public.aplicacao_questionario_id_seq', 24, true);


--
-- Name: avaliado_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qualigestor
--

SELECT pg_catalog.setval('public.avaliado_id_seq', 154, true);


--
-- Name: categoria_indicador_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qualigestor
--

SELECT pg_catalog.setval('public.categoria_indicador_id_seq', 1, false);


--
-- Name: cliente_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qualigestor
--

SELECT pg_catalog.setval('public.cliente_id_seq', 2, true);


--
-- Name: configuracao_cliente_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qualigestor
--

SELECT pg_catalog.setval('public.configuracao_cliente_id_seq', 1, true);


--
-- Name: foto_resposta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qualigestor
--

SELECT pg_catalog.setval('public.foto_resposta_id_seq', 26, true);


--
-- Name: grupo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qualigestor
--

SELECT pg_catalog.setval('public.grupo_id_seq', 86, true);


--
-- Name: integracao_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qualigestor
--

SELECT pg_catalog.setval('public.integracao_id_seq', 1, false);


--
-- Name: log_auditoria_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qualigestor
--

SELECT pg_catalog.setval('public.log_auditoria_id_seq', 323, true);


--
-- Name: notificacao_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qualigestor
--

SELECT pg_catalog.setval('public.notificacao_id_seq', 1, false);


--
-- Name: opcao_pergunta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qualigestor
--

SELECT pg_catalog.setval('public.opcao_pergunta_id_seq', 500, true);


--
-- Name: pergunta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qualigestor
--

SELECT pg_catalog.setval('public.pergunta_id_seq', 181, true);


--
-- Name: questionario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qualigestor
--

SELECT pg_catalog.setval('public.questionario_id_seq', 3, true);


--
-- Name: resposta_pergunta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qualigestor
--

SELECT pg_catalog.setval('public.resposta_pergunta_id_seq', 520, true);


--
-- Name: topico_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qualigestor
--

SELECT pg_catalog.setval('public.topico_id_seq', 22, true);


--
-- Name: usuario_autorizado_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qualigestor
--

SELECT pg_catalog.setval('public.usuario_autorizado_id_seq', 5, true);


--
-- Name: usuario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qualigestor
--

SELECT pg_catalog.setval('public.usuario_id_seq', 38, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: aplicacao_questionario aplicacao_questionario_pkey; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.aplicacao_questionario
    ADD CONSTRAINT aplicacao_questionario_pkey PRIMARY KEY (id);


--
-- Name: avaliado avaliado_pkey; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.avaliado
    ADD CONSTRAINT avaliado_pkey PRIMARY KEY (id);


--
-- Name: categoria_indicador categoria_indicador_pkey; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.categoria_indicador
    ADD CONSTRAINT categoria_indicador_pkey PRIMARY KEY (id);


--
-- Name: cliente cliente_pkey; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT cliente_pkey PRIMARY KEY (id);


--
-- Name: configuracao_cliente configuracao_cliente_pkey; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.configuracao_cliente
    ADD CONSTRAINT configuracao_cliente_pkey PRIMARY KEY (id);


--
-- Name: foto_resposta foto_resposta_pkey; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.foto_resposta
    ADD CONSTRAINT foto_resposta_pkey PRIMARY KEY (id);


--
-- Name: grupo grupo_pkey; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.grupo
    ADD CONSTRAINT grupo_pkey PRIMARY KEY (id);


--
-- Name: integracao integracao_pkey; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.integracao
    ADD CONSTRAINT integracao_pkey PRIMARY KEY (id);


--
-- Name: log_auditoria log_auditoria_pkey; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.log_auditoria
    ADD CONSTRAINT log_auditoria_pkey PRIMARY KEY (id);


--
-- Name: notificacao notificacao_pkey; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.notificacao
    ADD CONSTRAINT notificacao_pkey PRIMARY KEY (id);


--
-- Name: opcao_pergunta opcao_pergunta_pkey; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.opcao_pergunta
    ADD CONSTRAINT opcao_pergunta_pkey PRIMARY KEY (id);


--
-- Name: pergunta pergunta_pkey; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.pergunta
    ADD CONSTRAINT pergunta_pkey PRIMARY KEY (id);


--
-- Name: questionario questionario_pkey; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.questionario
    ADD CONSTRAINT questionario_pkey PRIMARY KEY (id);


--
-- Name: resposta_pergunta resposta_pergunta_pkey; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.resposta_pergunta
    ADD CONSTRAINT resposta_pergunta_pkey PRIMARY KEY (id);


--
-- Name: topico topico_pkey; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.topico
    ADD CONSTRAINT topico_pkey PRIMARY KEY (id);


--
-- Name: usuario_autorizado usuario_autorizado_pkey; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.usuario_autorizado
    ADD CONSTRAINT usuario_autorizado_pkey PRIMARY KEY (id);


--
-- Name: usuario usuario_email_key; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_email_key UNIQUE (email);


--
-- Name: usuario usuario_pkey; Type: CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_pkey PRIMARY KEY (id);


--
-- Name: aplicacao_questionario aplicacao_questionario_aplicador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.aplicacao_questionario
    ADD CONSTRAINT aplicacao_questionario_aplicador_id_fkey FOREIGN KEY (aplicador_id) REFERENCES public.usuario(id);


--
-- Name: aplicacao_questionario aplicacao_questionario_avaliado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.aplicacao_questionario
    ADD CONSTRAINT aplicacao_questionario_avaliado_id_fkey FOREIGN KEY (avaliado_id) REFERENCES public.avaliado(id);


--
-- Name: aplicacao_questionario aplicacao_questionario_questionario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.aplicacao_questionario
    ADD CONSTRAINT aplicacao_questionario_questionario_id_fkey FOREIGN KEY (questionario_id) REFERENCES public.questionario(id);


--
-- Name: avaliado avaliado_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.avaliado
    ADD CONSTRAINT avaliado_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.cliente(id);


--
-- Name: avaliado avaliado_grupo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.avaliado
    ADD CONSTRAINT avaliado_grupo_id_fkey FOREIGN KEY (grupo_id) REFERENCES public.grupo(id);


--
-- Name: categoria_indicador categoria_indicador_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.categoria_indicador
    ADD CONSTRAINT categoria_indicador_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.cliente(id);


--
-- Name: configuracao_cliente configuracao_cliente_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.configuracao_cliente
    ADD CONSTRAINT configuracao_cliente_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.cliente(id);


--
-- Name: foto_resposta foto_resposta_resposta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.foto_resposta
    ADD CONSTRAINT foto_resposta_resposta_id_fkey FOREIGN KEY (resposta_id) REFERENCES public.resposta_pergunta(id);


--
-- Name: grupo grupo_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.grupo
    ADD CONSTRAINT grupo_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.cliente(id);


--
-- Name: log_auditoria log_auditoria_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.log_auditoria
    ADD CONSTRAINT log_auditoria_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.cliente(id);


--
-- Name: log_auditoria log_auditoria_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.log_auditoria
    ADD CONSTRAINT log_auditoria_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: notificacao notificacao_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.notificacao
    ADD CONSTRAINT notificacao_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: opcao_pergunta opcao_pergunta_pergunta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.opcao_pergunta
    ADD CONSTRAINT opcao_pergunta_pergunta_id_fkey FOREIGN KEY (pergunta_id) REFERENCES public.pergunta(id);


--
-- Name: pergunta pergunta_topico_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.pergunta
    ADD CONSTRAINT pergunta_topico_id_fkey FOREIGN KEY (topico_id) REFERENCES public.topico(id);


--
-- Name: questionario questionario_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.questionario
    ADD CONSTRAINT questionario_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.cliente(id);


--
-- Name: questionario questionario_criado_por_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.questionario
    ADD CONSTRAINT questionario_criado_por_id_fkey FOREIGN KEY (criado_por_id) REFERENCES public.usuario(id);


--
-- Name: resposta_pergunta resposta_pergunta_aplicacao_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.resposta_pergunta
    ADD CONSTRAINT resposta_pergunta_aplicacao_id_fkey FOREIGN KEY (aplicacao_id) REFERENCES public.aplicacao_questionario(id);


--
-- Name: resposta_pergunta resposta_pergunta_pergunta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.resposta_pergunta
    ADD CONSTRAINT resposta_pergunta_pergunta_id_fkey FOREIGN KEY (pergunta_id) REFERENCES public.pergunta(id);


--
-- Name: topico topico_categoria_indicador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.topico
    ADD CONSTRAINT topico_categoria_indicador_id_fkey FOREIGN KEY (categoria_indicador_id) REFERENCES public.categoria_indicador(id);


--
-- Name: topico topico_questionario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.topico
    ADD CONSTRAINT topico_questionario_id_fkey FOREIGN KEY (questionario_id) REFERENCES public.questionario(id);


--
-- Name: usuario_autorizado usuario_autorizado_questionario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.usuario_autorizado
    ADD CONSTRAINT usuario_autorizado_questionario_id_fkey FOREIGN KEY (questionario_id) REFERENCES public.questionario(id);


--
-- Name: usuario_autorizado usuario_autorizado_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.usuario_autorizado
    ADD CONSTRAINT usuario_autorizado_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: usuario usuario_avaliado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_avaliado_id_fkey FOREIGN KEY (avaliado_id) REFERENCES public.avaliado(id);


--
-- Name: usuario usuario_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.cliente(id);


--
-- Name: usuario usuario_grupo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: qualigestor
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_grupo_id_fkey FOREIGN KEY (grupo_id) REFERENCES public.grupo(id);


--
-- PostgreSQL database dump complete
--

\unrestrict 4PkALt41hGrRjEhzBKaEl3y9aTLF3uOJJR4tedobnS5aCYcoKwlazIBXCs2NKTL

