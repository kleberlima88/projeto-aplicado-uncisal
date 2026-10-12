# 🏃‍♂️ Diário de Triatlo - Projeto Aplicado

**Disciplina:** Projeto Aplicado: Práticas de Mercado (Segurança da Informação)

Este repositório contém o protótipo de um sistema de acompanhamento de treinos para atletas de triatlo (Natação, Ciclismo, Corrida e Musculação). O projeto foi desenvolvido com foco na aplicação de conceitos de *Secure by Design* e *Secure by Default*, simulando o processamento de métricas de condicionamento físico através da leitura de dados exportados de smartwatches (Garmin). O sistema integra infraestrutura Cloud, automação CI/CD e auditoria assistida por Inteligência Artificial (Google Antigravity).

---

## 🛡️ Mitigações de Segurança (OWASP Top 10:2025)

Atendendo aos rigorosos requisitos do Eixo 3, o código-fonte deste projeto (Back-end em Python/Flask) foi estruturado para mitigar ativamente 3 vulnerabilidades críticas categorizadas pelo OWASP:

### 1. A01:2025 - Broken Access Control (Controlo de Acesso Quebrado)
* **Onde encontrar:** Ficheiro `app.py` (Rotinas `@app.before_request` e `@login_required`).
* **Como foi mitigado:** O sistema aplica o princípio de *Default Deny*. Todas as rotas internas são interceptadas globalmente e exigem uma sessão de servidor ativa e criptografada. A chave de sessão (`app.secret_key`) é injetada dinamicamente, impedindo ataques de falsificação de cookies. Qualquer tentativa de acesso desautenticado (ex: forçar o URL `/upload`) resulta no bloqueio imediato e redirecionamento seguro para a página de login.

### 2. A03:2025 - Injection & Insecure Design (Sanitização e Proteção de Uploads)
* **Onde encontrar:** Ficheiro `app.py` (Tratamento de uploads e renderização Pandas) e handler `413`.
* **Como foi mitigado:** A funcionalidade de importação de planilhas possui defesa em profundidade. O sistema restringe rigorosamente a extensão (apenas `.csv`) e impõe um limite máximo de 2MB (`MAX_CONTENT_LENGTH`) para prevenir ataques de negação de serviço (DoS). Os ficheiros são guardados no servidor com um prefixo criptográfico (`uuid.uuid4().hex`) para evitar sobrescrita ou *Race Conditions*. Além disso, os dados lidos pela biblioteca Pandas sofrem escape de entidades HTML (`escape=True`) antes de serem renderizados no `painel.html`, bloqueando qualquer tentativa de *Stored XSS* (Cross-Site Scripting) contida na folha de cálculo.

### 3. A07:2025 - Identification and Authentication Failures (Falhas de Autenticação e Força Bruta)
* **Onde encontrar:** Ficheiro `app.py` (Rota de `/login` e configuração de `ProxyFix`).
* **Como foi mitigado:** A rota de autenticação implementa um controlo estrito de *Rate Limiting*. Após 4 tentativas de acesso falhadas, o IP de origem é banido temporariamente (rejeitado com o código HTTP 429). Para garantir a eficácia desta medida atrás de um *Proxy Reverso* (Nginx), o sistema utiliza o middleware `ProxyFix`, bloqueando tentativas de *IP Spoofing* através da manipulação do cabeçalho `X-Forwarded-For`. A validação das credenciais é feita de forma segura utilizando `hmac.compare_digest`, neutralizando potenciais *Timing Attacks*.