-- AV2 Projeto Aplicado I — SQLite
-- Modelo com exatamente três entidades conforme roteiro Entrega 02.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tecnico_solicitante (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL CHECK (length(trim(nome)) > 0),
    papel TEXT NOT NULL CHECK (papel IN ('TECNICO', 'SOLICITANTE')),
    setor TEXT,
    matricula TEXT,
    ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    UNIQUE (nome, papel)
);

CREATE TABLE IF NOT EXISTS equipamento (
    id INTEGER PRIMARY KEY,
    tag TEXT NOT NULL UNIQUE CHECK (length(trim(tag)) > 0),
    codigo_origem TEXT,
    denominacao TEXT NOT NULL CHECK (length(trim(denominacao)) > 0),
    fabricante TEXT,
    fabricante_situacao TEXT CHECK (
        fabricante_situacao IS NULL OR
        fabricante_situacao IN ('INFORMADO', 'DESCONHECIDO', 'NAO_APLICAVEL')
    ),
    modelo TEXT,
    numero_serie TEXT,
    resolucao REAL CHECK (resolucao IS NULL OR resolucao >= 0),
    unidade_resolucao TEXT
);

CREATE TABLE IF NOT EXISTS medicao (
    id INTEGER PRIMARY KEY,
    codigo_evento TEXT NOT NULL CHECK (length(trim(codigo_evento)) > 0),
    equipamento_id INTEGER NOT NULL,
    tecnico_id INTEGER NOT NULL,
    solicitante_id INTEGER NOT NULL,
    data_medicao TEXT,
    data_calibracao TEXT,
    procedimento_codigo TEXT,
    procedimento_revisao INTEGER CHECK (procedimento_revisao IS NULL OR procedimento_revisao >= 0),
    padrao_informado TEXT,
    parametro TEXT NOT NULL CHECK (length(trim(parametro)) > 0),
    ordem INTEGER CHECK (ordem IS NULL OR ordem > 0),
    unidade TEXT NOT NULL DEFAULT 'mm',
    valor_nominal_mm REAL NOT NULL,
    tolerancia_superior_mm REAL NOT NULL,
    tolerancia_inferior_mm REAL NOT NULL,
    medida_1_mm REAL NOT NULL,
    medida_2_mm REAL NOT NULL,
    desvio_informado_1_mm REAL,
    desvio_informado_2_mm REAL,
    media_mm REAL NOT NULL,
    desvio_padrao_mm REAL CHECK (desvio_padrao_mm IS NULL OR desvio_padrao_mm >= 0),
    erro_mm REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDENTE'
        CHECK (status IN ('PENDENTE', 'EM_REVISAO', 'VALIDADA', 'EMITIDA')),
    origem_registro TEXT,
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    CHECK (valor_nominal_mm + tolerancia_inferior_mm <= valor_nominal_mm + tolerancia_superior_mm),
    UNIQUE (codigo_evento, parametro),
    FOREIGN KEY (equipamento_id) REFERENCES equipamento(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (tecnico_id) REFERENCES tecnico_solicitante(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (solicitante_id) REFERENCES tecnico_solicitante(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_medicao_equipamento_data
    ON medicao (equipamento_id, data_medicao);
CREATE INDEX IF NOT EXISTS idx_medicao_evento
    ON medicao (codigo_evento);

-- Garante que cada FK aponta para o papel correspondente no cadastro comum.
CREATE TRIGGER IF NOT EXISTS trg_medicao_papeis_insert
BEFORE INSERT ON medicao
WHEN
    (SELECT papel FROM tecnico_solicitante WHERE id = NEW.tecnico_id) <> 'TECNICO'
    OR
    (SELECT papel FROM tecnico_solicitante WHERE id = NEW.solicitante_id) <> 'SOLICITANTE'
BEGIN
    SELECT RAISE(ABORT, 'tecnico_id e solicitante_id devem apontar para seus papeis');
END;

CREATE TRIGGER IF NOT EXISTS trg_medicao_papeis_update
BEFORE UPDATE OF tecnico_id, solicitante_id ON medicao
WHEN
    (SELECT papel FROM tecnico_solicitante WHERE id = NEW.tecnico_id) <> 'TECNICO'
    OR
    (SELECT papel FROM tecnico_solicitante WHERE id = NEW.solicitante_id) <> 'SOLICITANTE'
BEGIN
    SELECT RAISE(ABORT, 'tecnico_id e solicitante_id devem apontar para seus papeis');
END;
