# ACERVO DOCUMENTAL - PROJETO RECOMEÇAR

---

## 1. TERMO DE ABERTURA DO PROJETO (TAP)

**Data de Emissão:** 13 de Novembro de 2026
**Nome do Projeto:** Plataforma Web "Recomeçar"
**Gestão de Documentação e Compliance:** IA Documentadora (Engenharia de Requisitos Sênior)

### 1.1. Justificativa e Objetivo do Projeto
O projeto "Recomeçar" visa mitigar a exclusão socioeconômica de mulheres egressas do sistema prisional brasileiro, promovendo sua reintegração ao mercado de trabalho formal e incentivando o empreendedorismo. O sistema atuará como uma ponte digital segura entre empresas parceiras (com vagas afirmativas) e egressas, além de prover uma "Vitrine Empreendedora" para comercialização de produtos artesanais. 

### 1.2. Escopo do Produto
*   **Módulo de Empregabilidade:** Matchmaking entre perfis de egressas e vagas cadastradas por empresas validadas.
*   **Módulo de Empreendedorismo (Vitrine):** Catálogo público para exposição de produtos artesanais criados pelas usuárias.
*   **Módulo de Autenticação e Autorização:** Sistema de login seguro baseado em e-mail, gerindo três perfis distintos (ADMIN, EGRESSA, EMPRESA).

### 1.3. Fora do Escopo (Limites de Compliance)
*   Integração com bases de dados de segurança pública, tribunais ou sistemas penitenciários.
*   Coleta, armazenamento ou processamento de qualquer dado de natureza criminal (artigos penais, tipificação de crimes, tempo de pena, comarca, histórico de processos).
*   Processamento de pagamentos on-platform (a vitrine funcionará como catálogo/vitrine de contato, mitigando riscos de gateway de pagamento no MVP).

### 1.4. Premissas de Compliance e Arquitetura (Privacy by Design)
*   **Desestigmatização (Diretrizes CNJ):** A validação do status da egressa será realizada estritamente via Autodeclaração Legal (Termo de Responsabilidade com aceite digital auditável).
*   **Anonimização:** A vitrine pública ocultará o nome civil completo da egressa, utilizando pseudônimos gerados (ex: primeiro nome da usuária + nome do ateliê/loja).
*   **Segurança Shift-Left:** Regras de LGPD e segurança da informação mapeadas e implementadas diretamente nas *constraints* e modelagem do banco de dados (Criptografia de dados em repouso, mascaramento de PII - *Personally Identifiable Information*).
*   **Filosofia de Entrega (Padrão IBM):** Orquestração orientada por governança de IA, com controle rigoroso de arquitetura e entregas sequenciadas.

### 1.5. Stack Tecnológica (MVP - Custo Zero de Infraestrutura)
*   **Backend:** Python 3.x com framework Django.
*   **Database:** PostgreSQL (hospedagem relacional serverless no Neon.tech).
*   **Frontend/UI:** Django Templates renderizados com Tailwind CSS (abordagem *utility-first*).
*   **Cloud/Deploy:** Plataforma Render (Tier gratuito para MVP).

---

## 2. DOCUMENTO DE ESPECIFICAÇÃO DE REQUISITOS (DER)

### 2.1. Atores do Sistema (Role-Based Access Control - RBAC)
O modelo `CustomUser` estenderá o usuário padrão do Django, utilizando o `email` como chave primária de autenticação e segregando permissões através das seguintes *roles*:
1.  **EGRESSA:** Usuária final que busca vagas ou publica produtos.
2.  **EMPRESA:** Entidade jurídica (com CNPJ validado) que publica e gerencia vagas.
3.  **ADMIN:** Gestor da plataforma (validação de denúncias, suporte técnico, moderação de conteúdo).

### 2.2. Requisitos Funcionais (RF)

| ID | Nome do Requisito | Descrição Técnica | Criticidade |
| :--- | :--- | :--- | :--- |
| **RF-01** | Autenticação Customizada | O sistema deve permitir login via e-mail e senha, utilizando um modelo `CustomUser` no Django, abolindo o uso de `username`. | Alta |
| **RF-02** | Cadastro de Egressa | O sistema deve permitir o cadastro de egressas contendo apenas: Nome civil, E-mail, Senha, Habilidades e o Aceite Digital do Termo de Autodeclaração. | Alta |
| **RF-03** | Cadastro de Empresa | O sistema deve permitir o cadastro de empresas mediante validação automática da situação cadastral do CNPJ (via API pública da Receita Federal/BrasilAPI). | Alta |
| **RF-04** | Gestão de Vagas | O perfil EMPRESA deve poder criar, editar, inativar e listar vagas de emprego. | Alta |
| **RF-05** | Aplicação em Vagas | O perfil EGRESSA deve poder visualizar vagas disponíveis e submeter interesse (aplicação). | Alta |
| **RF-06** | Vitrine Empreendedora | O perfil EGRESSA deve poder cadastrar produtos artesanais (título, descrição, foto, preço estimado e link de contato/WhatsApp). | Alta |
| **RF-07** | Anonimização Pública | O sistema deve renderizar o catálogo da Vitrine Empreendedora ocultando o sobrenome civil da EGRESSA, exibindo apenas um "Nome Social de Loja" ou primeiro nome. | Crítica (LGPD) |
| **RF-08** | Termo de Consentimento | O sistema deve registrar o *timestamp* e o IP anonimizado no momento do aceite dos Termos de Uso e Política de Privacidade (LGPD art. 8º). | Crítica (LGPD) |

### 2.3. Requisitos Não Funcionais (RNF)

| ID | Nome do Requisito | Descrição Técnica | Categoria |
| :--- | :--- | :--- | :--- |
| **RNF-01** | Conformidade LGPD | Zero armazenamento de dados sensíveis penais (Art. 5º, II da LGPD). Minimização de coleta de dados pessoais. | Legal/Segurança |
| **RNF-02** | Banco de Dados Relacional | Utilização de PostgreSQL (Neon) garantindo integridade referencial (ACID) e separação lógica por esquemas. | Infraestrutura |
| **RNF-03** | Arquitetura MVC/MVT | O código deve seguir estritamente o padrão Model-View-Template do Django, isolando regras de negócio no nível dos *Models* e *Services*. | Arquitetura |
| **RNF-04** | Responsividade (UI/UX) | A interface construída com Tailwind CSS deve ser *Mobile-First*, garantindo usabilidade em dispositivos móveis de baixo custo. | Usabilidade |
| **RNF-05** | Shift-Left Security | Proteção contra CSRF, XSS e SQL Injection nativa do Django habilitada. Senhas hasheadas utilizando algoritmo PBKDF2 ou Argon2. | Segurança |
| **RNF-06** | Escalabilidade de Custo | O MVP deve rodar integralmente em *Free Tiers* (Render/Neon) sem exceder limites de processamento (dynos) e conexões simultâneas de DB. | Desempenho |

### 2.4. Diagrama Lógico de Compliance e Validação (Shift-Left)

```text
[CLIENTE] --> Solicita Cadastro (EGRESSA)
    |
    |--> [MIDDLEWARE LGPD] Verifica payload de requisição.
    |       |--> SE (payload contém termos penais mapeados: 'artigo', 'pena', 'crime'):
    |       |       [!] REJEITA REQUISIÇÃO (HTTP 400 Bad Request) - Política Shift-Left
    |       |
    |       |--> SE (payload limpo):
    |               |--> Exige checkbox booleano: `is_autodeclarada = True`
    |               |--> [CONTROLLER] Processa Hasheamento de senha
    |               |--> [DATABASE] Salva usuário com minimização de dados.