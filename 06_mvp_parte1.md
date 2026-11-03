# AV03 · Calibração de dispositivos de controle
**Maria Claudia Cabral da Silva · UniSENAI · Projeto Aplicado I · 2026.2**  
Empresa parceira: Schulz S.A. | Docentes: Hugo Menezes Barra e Rodrigo Losina.

## Executar e reproduzir
Com Python 3.10 ou superior, abra esta pasta no VS Code e execute no terminal:

~~~text
python 05_main.py
python -m unittest -v
~~~

O primeiro comando cria um arquivo SQLite temporário, executa o SQL entregue na AV2 e imprime a consulta. Para conservar os registros, use `python 05_main.py --banco demonstracao.sqlite`. Cada execução cria um novo evento e novos cadastros fictícios. Utilize uma base de demonstração; não é necessária conexão externa ou instalação de bibliotecas Python.

## Modelo de objetos e correspondência com a AV2
O roteiro descreve as entidades no plural. O MVP usa os nomes físicos reais de `03_banco.sql`, preservado sem alteração. As três classes de domínio são objetos imutáveis: a construção valida os campos, e uma alteração gera uma nova representação antes da persistência. Não há necessidade de herança entre as entidades. A composição acontece na demonstração, que coordena os objetos e o repositório.

~~~mermaid
classDiagram
    class Tecnico {
        +nome
        +matricula
        +setor
        +papel
        +ativo
    }
    class Equipamento {
        +tag
        +denominacao
        +fabricante
    }
    class Medicao {
        +codigo_evento
        +parametro
        +medida_1_mm
        +medida_2_mm
        +media
        +erro
        +resultado
        +status
    }
    class Banco {
        +preparar()
        +salvar(obj)
        +buscar(classe, id)
        +excluir(classe, id)
        +relatorio(evento)
    }
    Tecnico "1" <-- "0..*" Medicao : executa
    Tecnico "1" <-- "0..*" Medicao : solicita
    Equipamento "1" <-- "0..*" Medicao : medido
    Banco ..> Tecnico
    Banco ..> Equipamento
    Banco ..> Medicao
~~~

- **Tecnico → tecnico_solicitante:** o cadastro comum da AV2 distingue o profissional e a unidade solicitante por papel. Matrícula é texto e conserva zeros à esquerda.
- **Equipamento → equipamento:** TAG única e denominação obrigatória identificam o dispositivo.
- **Medicao → medicao:** uma linha por evento e parâmetro; exige duas leituras em mm, incluindo repetições idênticas. Os campos opcionais da AV2 fora deste recorte não são sobrescritos nas atualizações.
- **Banco:** concentra conexões, mapeamento objeto-relacional, comandos parametrizados e transações. O arquivo inicial se chama `04_classes.py` conforme o roteiro; o principal carrega esse módulo com `importlib`, pois um identificador Python não pode começar por dígito.

## Decisão do ensaio
A média das duas leituras menos o nominal é o erro. Se o erro pertence ao intervalo fechado dos afastamentos inferior e superior, o resultado é APROVADO; caso contrário, REPROVADO. A comparação usa Decimal sobre a representação decimal das leituras, antes da formatação da saída. A persistência segue os campos REAL da AV2. Valores ausentes, não finitos e afastamentos invertidos são rejeitados.

A classificação é calculada sob demanda; o campo físico `status` continua a indicar o fluxo documental. Um ensaio aprovado pode estar EM_REVISAO. A regra didática não decide a liberação industrial do equipamento, não incorpora incerteza e não emite um certificado.

## Persistência e falhas
`salvar` insere um objeto sem ID ou atualiza uma linha existente; `buscar` reconstrói o objeto; `excluir` respeita referências; `relatorio` combina medicao, equipamento e dois papéis de tecnico_solicitante. Cada operação abre uma conexão, habilita FKs, confirma a transação após sucesso e fecha a conexão. Em erro, a transação de escrita é revertida. Violações SQL geram ErroPersistencia com a exceção original como causa. Dados inválidos geram ValueError; ID não localizado gera KeyError.

## Validação funcional
Com nominal 10,000 mm e afastamentos ±0,050 mm:

| Parâmetro | Leituras (mm) | Média | Erro | Ensaio | Documento |
|---|---|---:|---:|---|---|
| Diâmetro A | 10,020 e 10,040 | 10,030 | +0,030 | APROVADO | EM_REVISAO |
| Diâmetro B | 10,060 e 10,080 | 10,070 | +0,070 | REPROVADO | PENDENTE |

Os cinco testes de integração e domínio em `test_mvp.py` cobrem limites inclusivos, reprovação nos dois lados, dados inválidos, consultas com JOIN, recálculo após UPDATE, exclusão, duplicidade, papel incorreto, referência inexistente e reversão de falhas. A demonstração conserva as leituras de origem; importação das planilhas, reconciliação do padrão, auditoria e geração do certificado completo ficam para etapas posteriores.

## Fontes do projeto
AV1 de Maria Claudia Cabral da Silva (regras de repetição, tolerância e separação entre ensaio e emissão); AV2_Projeto_Aplicado_I.zip (dicionário e DDL oficial da entrega); AV03 - Projeto Aplicado I Roteiro.pdf (itens 2 a 4).
