# Recomeçar

> **Talento que transforma.**
>
> Plataforma web que conecta mulheres egressas do sistema prisional a oportunidades de emprego, empreendedorismo e capacitação — com foco em reinserção social, dignidade e conformidade LGPD.

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.1-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Tailwind](https://img.shields.io/badge/Tailwind-3.4-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/tests-274%20passing-brightgreen)](https://github.com/mfsc3/recomecar)
[![LGPD](https://img.shields.io/badge/LGPD-compliant-blue)](https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd)

---

## 📌 Sobre o projeto

O Recomeçar é uma plataforma de empregabilidade voltada a um público historicamente excluído do mercado formal: **mulheres egressas do sistema prisional**. O sistema cobre o ciclo completo:

- **Egressa:** cadastro verificado, currículo modular, busca de vagas, candidatura com snapshot imutável, vitrine de produtos (empreendedorismo).
- **Empresa:** perfil institucional verificado, publicação de vagas, acesso a candidatas com currículo renderizado em tela.
- **Administração:** aprovação de empresas, moderação, direito ao esquecimento (LGPD Art. 18).

### Por que este projeto é diferente

Três decisões moldam toda a arquitetura:

1. **Compliance é requisito de engenharia, não checkbox.** Nenhuma tabela, coluna ou `help_text` armazena histórico penal, artigos, regime ou tempo de pena. A restrição é aplicada no design do banco, não em validação de formulário. Toda sprint passa por grep de compliance antes do merge.
2. **Imutabilidade onde importa.** Uma candidatura guarda um **snapshot JSON do currículo** no momento do envio. Edições posteriores da egressa **não** alteram o que a empresa vê. Isso resolve auditoria e evita disputas "você aplicou com esse currículo" / "não apliquei".
3. **Segurança por padrão.** Anti-IDOR em todas as relações (egressa↔egressa, empresa↔empresa), CSP estrita, `django-axes` para brute force, hard delete em cascata com testes que provam zero órfãos, vínculo social apenas para e-mail verificado (anti pre-hijacking).

---

## 🎯 Funcionalidades

### Autenticação e identidade
- Login por **e-mail** (não por username), `CustomUser` com RBAC (`ADMIN`, `EGRESSA`, `EMPRESA`)
- **Verificação de e-mail obrigatória** no cadastro local (conta nasce `is_active=False`, ativa via signal do `allauth`)
- **Google OAuth** integrado — cria conta apenas para EGRESSA, vincula a contas existentes **somente** se o e-mail local estiver verificado
- **Recuperação de senha** com resposta anti-enumeração (a mesma mensagem exista ou não o e-mail)
- **Bloqueio de força bruta** (`django-axes`): 5 falhas por IP+usuário → 15 min de lockout, sem revelar se a conta existe
- Logout **apenas via POST** (Django 5+)

### Perfis
- **Egressa:** currículo modular (resumo, habilidades, experiências, escolaridades), candidaturas
- **Empresa:** razão social, nome fantasia, CNPJ validado por dígito verificador, logo (R2), endereço estruturado, responsável, telefone, descrição institucional
- **Aprovação de empresa** pelo ADMIN — empresa não aprovada não publica vagas (mas mantém acesso às candidaturas já recebidas, por LGPD)

### Vagas e candidaturas
- Listagem pública **apenas** de vagas ativas de empresas aprovadas
- CRUD de vagas **protegido contra IDOR** (`get_object_or_404(Vaga, pk=..., empresa=perfil_do_usuario)` — 404, nunca 403)
- **Candidatura exige currículo** — redireciona para preencher, com `messages.warning`
- **Snapshot imutável** do currículo gravado no momento da candidatura
- Empresa vê **apenas e-mail + data** de quem se candidatou + snapshot do currículo (via `.values()` restrito)

### LGPD
- **Direito ao esquecimento** (Art. 18): exclusão definitiva da conta, com cascade testado nas duas direções (empresa excluída → vagas e candidaturas; egressa excluída → currículo, experiências, escolaridades, candidaturas)
- **Prova de consentimento:** `aceitou_termo_em` + `versao_termo` (versionado), `aceitou_compartilhar_em` por candidatura
- **Minimização de dados:** `extra_data` do Google é zerado a cada login
- **Zero** campos de histórico penal, antecedentes ou avaliação comportamental

### Segurança frontend
- **CSP estrita** via `django-csp` (`default-src 'self'`, sem `unsafe-inline`/`unsafe-eval`; `/admin/` excluído por usar JS inline)
- **Tailwind build local** (sem CDN, sem dependência externa)
- **Favicon + logos SVG** servidos pelo WhiteNoise
- **Rate limit** em recuperação de senha (5/h por IP, 3/h por e-mail) e reenvio de confirmação

---

## 🏗️ Stack

| Camada | Tecnologia |
|-----|-----|
| **Backend** | Python 3.14, Django 6.1.3 |
| **Banco** | PostgreSQL 16 (Neon) |
| **Frontend** | Tailwind CSS 3.4.17 (build local via CLI), HTML server-side |
| **Auth** | django-allauth 65.22 (Google OAuth + verificação de e-mail), django-axes (brute force) |
| **Storage** | Cloudflare R2 via django-storages 1.14 (S3-compatible) |
| **E-mail** | Brevo SMTP (produção), console backend (dev) |
| **Segurança** | django-csp, CSRF, sessões seguras, HSTS em produção |
| **Deploy** | Render (free tier), WhiteNoise, Gunicorn |
| **Testes** | Django test runner, 274 testes, SQLite em memória |

---

## 🧠 Desafios técnicos resolvidos

Alguns dos problemas que exigiram decisões arquiteturais específicas:

### 1. Snapshot imutável de currículo (`accounts/services.py`)

**Problema:** se a empresa acessa o currículo da candidata via FK, edições futuras alteram o que ela vê — perda de auditoria e risco de disputa.
**Solução:** `Candidatura.curriculo_snapshot = JSONField()` capturado no `CandidatarView.post()` via função pura `snapshot_curriculo()`. Testes provam que editar o currículo após candidatura **não altera** o snapshot.
**Trade-off:** duplicação de dados no banco (~2KB por candidatura) em troca de integridade histórica.

### 2. Guard fail-loud de storage (`config/settings.py`)

**Problema:** em produção, se R2 não estiver configurado, o Django cai em `FileSystemStorage` **silenciosamente** — logos somem a cada redeploy (disco efêmero).
**Solução:** função pura `_validate_storage_backend(debug, backend, is_test)` que levanta `ImproperlyConfigured` no startup se `DEBUG=False` e o backend for `FileSystemStorage`. Testável sem reload do módulo.

### 3. Anti pre-hijacking no login social (`accounts/adapters.py`)

**Problema:** atacante cadastra e-mail da vítima com senha própria; quando a vítima entra com Google, o allauth vincula as contas e o atacante mantém acesso.
**Solução:** `SOCIALACCOUNT_EMAIL_AUTHENTICATION=False` + `pre_social_login` que **só vincula** se existir `EmailAddress.verified=True` para aquele e-mail. Caso contrário, bloqueia com mensagem genérica.

### 4. Vínculo Google + verificação de e-mail em fluxo único

**Problema:** a verificação de e-mail do cadastro local (Sprint 6.1) destravava o vínculo social — mas precisava ser feita **sem** quebrar o fluxo existente de login social.
**Solução:** signal `email_confirmed` do allauth ativa `is_active` + `EmailAddress.verified` libera o vínculo social. Dois fluxos que pareciam independentes passaram a se reforçar.

### 5. `full_clean()` em `save()` de models com validação cruzada

**Problema:** `limit_choices_to` no `ForeignKey` só filtra no admin/form — não impede criação programática (`Candidatura` com `candidata` EMPRESA, por exemplo).
**Solução:** `EmpresaProfile` e `Candidatura` chamam `self.full_clean()` no `save()`. Custo: `save()` mais lento. Benefício: impossível gravar estado inválido via shell, view, admin ou API.

---

## 🧪 Testes

```bash
python manage.py test
# Ran 274 tests in ~10s
# OK (2 skipped: SMTP em produção, esperado com DEBUG=True)

```

Cobertura dos caminhos críticos:

* **Anti-IDOR:** egressa acessando currículo de outra, empresa acessando candidatura de outra (404 nas duas direções)
* **Cascade + LGPD:** exclusão de conta sem órfãos, com não contaminação cruzada entre empresas/egressas
* **Snapshot imutável:** edição do currículo após candidatura não altera o snapshot
* **CSP:** header presente em rotas públicas, ausente em `/admin/`, sem `unsafe-*`
* **Guard de storage:** dispara com `DEBUG=False+FS`, não dispara com `DEBUG=True`/R2/modo teste
* **Rate limit:** bloqueio por IP e por e-mail, resposta anti-enumeração
* **Atomicidade:** falha no envio de e-mail não quebra o cadastro (rollback garantido)
* **Fluxo ponta a ponta:** cadastro → verificação → aprovação → vaga → candidatura → snapshot

---

## 🚀 Como rodar localmente

### Pré-requisitos

* Python 3.12+ (recomendado 3.14)
* PostgreSQL 16 **ou** SQLite (dev rápido)
* `git`

### Setup

```bash
# 1. Clone
git clone [https://github.com/mfsc3/recomecar.git](https://github.com/mfsc3/recomecar.git)
cd recomecar

# 2. Ambiente virtual
python -m venv venv
source venv/bin/activate          # Linux/Mac
# venv\Scripts\activate           # Windows

# 3. Dependências
pip install -r requirements.txt

# 4. Variáveis de ambiente
cp .env.example .env
# Edite .env com: SECRET_KEY, DATABASE_URL, R2_* (opcional), EMAIL_* (opcional)

# 5. Build do CSS (Tailwind)
bash scripts/build_css.sh         # Linux/Mac
# powershell -ExecutionPolicy Bypass -File scripts\build_css.ps1  # Windows

# 6. Banco
python manage.py migrate
python manage.py createsuperuser

# 7. Rodar
python manage.py runserver

```

Acesse `http://127.0.0.1:8000/`.

### Rodar testes

```bash
python manage.py test

```

> Os testes usam SQLite em memória — não tocam no PostgreSQL nem no R2 real.

---

## 📁 Estrutura

```
recomecar/
├── accounts/              # CustomUser, currículo, auth views, adapters, signals
├── vagas/                 # EmpresaProfile, Vaga, Candidatura, perfil de empresa
├── vitrine/               # Produtos/serviços das egressas
├── config/                # settings, urls, tests de config
├── templates/             # base.html + templates por app
├── static/                # CSS compilado, imagens, logos
├── static_src/            # input.css do Tailwind
├── scripts/               # build_css.sh / build_css.ps1
├── tailwind.config.js
├── requirements.txt
└── manage.py

```

---

## 🔒 Segurança — checklist aplicado

* [x] Sem `unsafe-inline` ou `unsafe-eval` na CSP
* [x] `SECRET_KEY` e credenciais via `.env` (nunca commitados)
* [x] `.env.example` com valores fictícios apenas
* [x] Anti-IDOR com filtro no banco (não em `if` após `get()`)
* [x] `transaction.atomic()` com `try/except` fora do bloco (rollback garantido)
* [x] `full_clean()` em models com validação cruzada
* [x] `axes` configurado com lockout por IP+usuário (sem enumeração)
* [x] Logs nunca contêm e-mail, senha ou `request.POST`
* [x] `DEFAULT_AUTO_FIELD` explícito, sem `id` previsível em rotas públicas
* [x] Sem `|safe` ou `autoescape off` em templates
* [x] Hard delete com cascade testado (zero órfãos)

---

## 📝 Processo de desenvolvimento e IA

Este projeto foi construído utilizando um modelo avançado de **Desenvolvimento Orientado por IA (AI-Driven Development)**, onde a engenharia de software foi orquestrada por uma triagem de responsabilidades entre humano e inteligências artificiais:

1. **Orquestração Humana (Tech Lead/Product):** Responsável por definir a visão do produto, requisitos de negócio, gerenciar as sprints, aprovar a lógica de domínio e garantir que o propósito social (e as sensibilidades da LGPD) fossem o pilar central.
2. **IA Cérebro / Arquiteta (LLM Consultivo):** Responsável por idealizar a arquitetura Django, desenhar os *Blueprints técnicos* de cada sprint antes da escrita de código, modelar o banco de dados seguro, estabelecer os fluxos anti-IDOR e realizar auditorias (code reviews) detalhadas após cada implementação.
3. **IA Engenheira / Executora (LLM de Código):** Responsável por escrever o código-fonte, implementar as lógicas de backend, estilizar o frontend com Tailwind e gerar a densa suíte de testes automatizados, seguindo estritamente os blueprints fornecidos pela IA Cérebro.

### O Fluxo de Trabalho (Blueprints + Dupla-checagem)

Em vez de gerar código diretamente, o processo seguiu um rigoroso padrão:

* **Blueprints detalhados** gerados pela IA Cérebro antes de cada sprint (modelagem, segurança, URLs, testes e prompts para execução).
* **Execução guiada** pela IA Engenheira.
* **Auditoria read-only** após cada execução (review de código cruzado entre IAs e humano antes do merge).
* **Grep de compliance** (`antecedentes`, `pena`, `artigo`, `regime`, etc.) em todo PR.
* **Zero merges sem testes verdes.**

Essa separação de papéis garantiu que a velocidade da IA não comprometesse a segurança e a arquitetura do projeto. O processo capturou **5 bugs no próprio blueprint** ao longo das sprints, todos corrigidos antes de chegar à produção. Nenhum bug de segurança chegou à branch `main`.

---

## 🗺️ Roadmap

Já entregue (Sprints 1–10 + mini-sprints 4.1, 8.1, 6.1):

* ✅ Autenticação + RBAC + verificação de e-mail + Google OAuth
* ✅ Perfis de egressa e empresa
* ✅ Vagas, candidaturas e snapshots
* ✅ Currículo modular
* ✅ LGPD (direito ao esquecimento, consentimento versionado)
* ✅ CSP, Tailwind local, guard de R2, brute force

Backlog pós-lançamento:

* [ ] CI com PostgreSQL (hoje SQLite em memória)
* [ ] Auditoria de exclusão de conta (prova de LGPD)
* [ ] Pre-commit hook para rebuild automático do CSS
* [ ] Moderação de conteúdo em descrições de vagas
* [ ] Soft-delete com janela de 30 dias (recuperação de conta)
* [ ] CSP com nonce para `/admin/`
* [ ] Foto/avatar da egressa (com consentimento explícito)
* [ ] Recuperação de senha para contas sociais (sem senha utilizável)

---

## 📄 Licença

Distribuído sob licença **MIT**. Veja [`LICENSE`](https://www.google.com/search?q=LICENSE) para detalhes.

O código é público para portfólio e aprendizado. Uso comercial em produção requer conversa com o autor.

---

## 👤 Autor

**Marcos Fábio de Souza Carvalho** ([@mfsc3](https://github.com/mfsc3))

Projeto desenvolvido como parte de portfólio técnico, com foco em **Django, segurança de aplicação, LGPD, impacto social e colaboração humano-IA**.

---

## 🙏 Agradecimentos

Às mulheres que inspiraram este projeto. Que toda mulher tenha a oportunidade de construir uma nova história.

```

---

### Como aplicar:
Abra o seu arquivo `README.md`, selecione tudo (`Ctrl+A`), apague e cole esse novo conteúdo. 

Depois, é só subir para o GitHub:
```bash
git add README.md
git commit -m "docs: adiciona fluxo de AI-driven development no README"
git push origin main

```
