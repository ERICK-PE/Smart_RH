Create database Smart RH

Use Smart RH

CREATE TABLE cargo (
    id_cargo SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT
);
CREATE TABLE setor (
    id_setor SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT
);
CREATE TABLE funcionario (
    id_funcionario SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    email VARCHAR(150) UNIQUE,
    telefone VARCHAR(20),
    data_admissao DATE NOT NULL,

    fk_id_setor INT NOT NULL,
    fk_id_cargo INT NOT NULL,

    FOREIGN KEY (fk_id_setor) REFERENCES setor(id_setor),
    FOREIGN KEY (fk_id_cargo) REFERENCES cargo(id_cargo)
);

CREATE TABLE contrato (
    id_contrato SERIAL PRIMARY KEY,
    fk_id_funcionario INT NOT NULL,

    tipo_contrato VARCHAR(50),
    salario NUMERIC(10,2),
    data_inicio DATE NOT NULL,
    data_fim DATE,

    FOREIGN KEY (fk_id_funcionario) REFERENCES funcionario(id_funcionario)
);

CREATE TABLE avaliacao_desempenho (
    id_avaliacao SERIAL PRIMARY KEY,

    fk_id_funcionario INT NOT NULL,      -- avaliado
    fk_id_avaliador INT NOT NULL,        -- quem avalia

    categoria VARCHAR(100),
    nota NUMERIC(5,2),
    comentario TEXT,
    data_avaliacao DATE NOT NULL,

    FOREIGN KEY (fk_id_funcionario) REFERENCES funcionario(id_funcionario),
    FOREIGN KEY (fk_id_avaliador) REFERENCES funcionario(id_funcionario)
);

CREATE TABLE analise_comportamental (
    id_analise SERIAL PRIMARY KEY,
    fk_id_funcionario INT NOT NULL,

    resultado TEXT,
    data_analise DATE,

    FOREIGN KEY (fk_id_funcionario) REFERENCES funcionario(id_funcionario)
);

CREATE TABLE plano_carreira (
    id_plano SERIAL PRIMARY KEY,
    fk_id_cargo INT NOT NULL,

    descricao TEXT,
    requisitos TEXT,

    FOREIGN KEY (fk_id_cargo) REFERENCES cargo(id_cargo)
);

CREATE TABLE vaga (
    id_vaga SERIAL PRIMARY KEY,
    titulo VARCHAR(150),
    descricao TEXT,
    data_publicacao DATE,

    fk_id_setor INT,

    FOREIGN KEY (fk_id_setor) REFERENCES setor(id_setor)
);

CREATE TABLE candidato (
    id_candidato SERIAL PRIMARY KEY,
    nome VARCHAR(150),
    email VARCHAR(150),
    telefone VARCHAR(20),
    curriculo TEXT
);

CREATE TABLE candidato_vaga (
    id_candidato INT,
    id_vaga INT,
    status_processo VARCHAR(50),

    PRIMARY KEY (id_candidato, id_vaga),

    FOREIGN KEY (id_candidato) REFERENCES candidato(id_candidato),
    FOREIGN KEY (id_vaga) REFERENCES vaga(id_vaga)
);