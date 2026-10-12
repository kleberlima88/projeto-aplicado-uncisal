## 🛡️ Mitigações de Segurança (OWASP Top 10:2025)

Atendendo aos rigorosos requisitos do Eixo 3 e adotando uma postura de *Defense in Depth* (Defesa em Profundidade), o código-fonte e a infraestrutura deste projeto foram arquitetados para mitigar ativamente 7 vulnerabilidades críticas categorizadas pela mais recente versão oficial do OWASP (Top 10:2025):

### 1. A01:2025 - Broken Access Control (Controlo de Acesso Quebrado)
* **Onde encontrar:** Ficheiro `app.py` (Rotinas `@app.before_request` e `@login_required`).
* **Como foi mitigado:** O sistema aplica o princípio de *Default Deny*. Todas as rotas internas são interceptadas globalmente e exigem uma sessão de servidor ativa. A chave de sessão é injetada dinamicamente, impedindo ataques de falsificação de cookies. Qualquer tentativa de acesso desautenticado resulta no bloqueio imediato e redirecionamento para a página de login.

### 2. A02:2025 - Security Misconfiguration (Má Configuração de Segurança)
* **Onde encontrar:** Infraestrutura e Ficheiro `app.py` (Final do ficheiro e gestão de variáveis).
* **Como foi mitigado:** O sistema está configurado para o ambiente de produção com o modo de depuração desativado (`app.run(debug=False)`), o que previne o vazamento de *stack traces* e código-fonte no navegador. Além disso, as credenciais e chaves de API reais foram isoladas num ficheiro `.env` não versionado no GitHub, impedindo a exposição acidental de segredos.

### 3. A04:2025 - Cryptographic Failures (Falhas Criptográficas)
* **Onde encontrar:** Servidor Oracle Cloud e configuração do Nginx.
* **Como foi mitigado:** Os dados sensíveis dos atletas (como saúde e credenciais) não transitam em texto limpo. O tráfego do painel é integralmente encriptado de ponta a ponta via HTTPS, com certificados SSL geridos pelo Certbot. Isto neutraliza o risco de ataques *Man-in-the-Middle* (MitM) em redes públicas.

### 4. A05:2025 - Injection (Injeção e Cross-Site Scripting)
* **Onde encontrar:** Ficheiro `app.py` (Tratamento de leitura de dados e escape HTML).
* **Como foi mitigado:** Para garantir que ficheiros manipulados não executem scripts maliciosos no *front-end*, os dados extraídos das planilhas `.csv` sofrem sanitização estrita. Entidades HTML são neutralizadas (`escape=True` no Pandas e `html.escape` no fallback nativo) antes da renderização no ecrã, bloqueando injeções de *Stored XSS*.

### 5. A06:2025 - Insecure Design (Design Inseguro e Proteção de Arquivos)
* **Onde encontrar:** Ficheiro `app.py` (Tratamento de uploads e limites).
* **Como foi mitigado:** A aplicação prevê falhas físicas no *design*. Existe um limite máximo de 2MB (`MAX_CONTENT_LENGTH`) para uploads, prevenindo negação de serviço (DoS) por esgotamento de disco. Os ficheiros guardados recebem um prefixo estocástico (`uuid.uuid4().hex`), o que impossibilita a sobrescrita intencional de ficheiros de outros utilizadores e previne *Race Conditions*.

### 6. A07:2025 - Authentication Failures (Falhas de Autenticação)
* **Onde encontrar:** Ficheiro `app.py` (Rota de `/login` e configuração de `ProxyFix`).
* **Como foi mitigado:** Foi implementado *Rate Limiting* rigoroso: após 4 tentativas falhadas, o IP de origem é banido temporariamente (HTTP 429). Para que o bloqueio funcione atrás do *Proxy Reverso* (Nginx), utilizou-se o `ProxyFix` para impedir *IP Spoofing*. Adicionalmente, a validação de senhas usa `hmac.compare_digest` para anular vulnerabilidades de *Timing Attacks*.

### 7. A10:2025 - Mishandling of Exceptional Conditions (Tratamento Inadequado de Exceções)
* **Onde encontrar:** Ficheiro `app.py` (Blocos `try/except` e `@app.errorhandler(413)`).
* **Como foi mitigado:** A aplicação lida com cenários adversos de forma graciosa. Exceções críticas, como ficheiros excessivamente grandes ou falhas de comunicação com a API da Inteligência Artificial (DeepSeek/Groq), são intercetadas. Em vez de travar o servidor ou expor erros ao utilizador, o sistema emite mensagens visuais amigáveis (`flash`), mantendo a estabilidade e a segurança da interface.