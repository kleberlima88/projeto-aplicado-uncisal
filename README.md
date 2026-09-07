# 🏃‍♂️ Diário de Triatlo - Projeto Aplicado
**Disciplina:** Projeto Aplicado: Práticas de Mercado (Segurança da Informação)

Este repositório contém o protótipo de um sistema de acompanhamento de treinos para atletas de triatlo (Natação, Ciclismo, Corrida e Musculação). O projeto foi desenvolvido com foco na aplicação de conceitos de *Secure by Design*, simulando o registro de métricas de condicionamento e sincronização de dados de smartwatches (ex: Garmin).

## 🛡️ Mitigações de Segurança (OWASP Top 10)

Atendendo aos requisitos do Eixo 3, o código-fonte deste projeto mitiga ativamente 3 vulnerabilidades categorizadas pelo OWASP:

### 1. A03:2021 - Injection (Prevenção contra XSS e Injeção de Código)
* **Onde encontrar:** Arquivo `index.html` (Linha 35)
* **Como foi mitigado:** A função de login possui uma validação baseada em Expressão Regular (`/^[a-zA-Z0-9]+$/`) que atua como um filtro rigoroso de sanitização (Allowlist). Ela bloqueia a entrada de caracteres especiais (`<`, `>`, `'`, `"`), impedindo ataques de injeção de scripts maliciosos pelo lado do cliente.

### 2. A01:2021 - Broken Access Control (Quebra de Controle de Acesso)
* **Onde encontrar:** Arquivos `index.html` (Linha 42) e `dashboard.html` (Linha 41)
* **Como foi mitigado:** O acesso à página interna (`dashboard.html`) é protegido por uma verificação de sessão. Durante o login bem-sucedido, um token virtual é gerado no `sessionStorage`. Se um usuário tentar acessar o painel do atleta diretamente pela URL sem este token, o sistema bloqueia o acesso e o redireciona de volta para a tela de autenticação.

### 3. A04:2021 - Insecure Design (Validação Rigorosa de Upload de Arquivos)
* **Onde encontrar:** Arquivo `dashboard.html` (Linha 63)
* **Como foi mitigado:** A funcionalidade de importação de planilhas de treino do relógio esportivo possui uma dupla trava de segurança. O sistema verifica a extensão do arquivo (permitindo exclusivamente `.gpx`, `.tcx` e `.csv`) e limita o tamanho máximo do upload a 2MB. Isso previne que invasores façam o upload de executáveis disfarçados ou scripts que possam comprometer o sistema.
