# Cinema Clássicos SP

Avisa no ntfy quando algum filme da sua lista (`movies.json`) entra em cartaz em cinemas de São Paulo capital
e mantém uma página com filmes, cinemas, datas e horários. Fonte: Ingresso.com (Cinemark, Cinépolis, UCI, Kinoplex...).

## Rodar na nuvem (GitHub) — sem depender do PC

A busca roda sozinha no GitHub às **00:07 e 12:07** (horário de Brasília), avisa no ntfy e publica a página
em `https://renanvamo.github.io/scrapping-cinema/`.

### Configuração (uma vez só)
Repositório: https://github.com/renanvamo/scrapping-cinema (branch `master`).
Página: https://renanvamo.github.io/scrapping-cinema/

1. **Enviar o projeto.** Na pasta do projeto, no PowerShell (o 1º e o 2º comando colocam o arquivo da tarefa agendada
   na pasta que o GitHub exige: `.github\workflows`, com **s**):
   ```
   New-Item -ItemType Directory -Force .github\workflows | Out-Null
   Move-Item workflow-buscar.yml .github\workflows\buscar.yml
   git init
   git add .
   git commit -m "Primeiro commit"
   git branch -M master
   git remote add origin https://github.com/renanvamo/scrapping-cinema.git
   git push -u origin master --force
   ```
   O `--force` substitui o que já está no repositório (só o `buscar.yml` criado na pasta `workflow`, sem **s**),
   o que é o esperado. Se o `git commit` pedir "tell me who you are", rode antes:
   `git config --global user.name "Seu Nome"` e `git config --global user.email "seu@email.com"`.
   Seu tópico do ntfy fica só em `config.local.json`, que está no `.gitignore` e **não** sobe.
2. **Secret do ntfy.** No repositório: **Settings → Secrets and variables → Actions → New repository secret**.
   Nome: `NTFY_TOPIC` — Valor: o seu tópico do ntfy.
3. **Ativar a página.** **Settings → Pages → Build and deployment**: Source = *Deploy from a branch*,
   Branch = `master`, pasta `/docs` → Save. (A pasta `/docs` só aparece depois da primeira busca com sucesso.)
4. **Testar.** **Actions → Buscar clássicos → Run workflow**, escolha `testar`: mostra o log de cada cinema
   (se o GitHub for bloqueado pelo Ingresso.com, aparece como `HTTP 403`). Depois rode com `buscar`.
5. Se criou a tarefa do Windows, remova-a para não receber avisos duplicados:
   `schtasks /Delete /TN CinemaClassicos /F`

### Pausar / retomar
**Actions → Buscar clássicos → botão `⋯` (canto superior direito) → Disable workflow.**
Para voltar: o mesmo caminho, **Enable workflow**. A página continua no ar com a última busca.
Para apagar tudo: Settings → *Delete this repository*.

### Bom saber
- O GitHub pode atrasar tarefas agendadas em alguns minutos, e desativa agendamentos de repositórios sem atividade
  por 60 dias. Se parar de rodar, reative em Actions.
- Se uma busca falhar (fonte fora do ar/bloqueada), a execução aparece em vermelho, o GitHub avisa por e-mail,
  e a página anterior é mantida.
- Alterar a lista de filmes: edite `movies.json` (no GitHub mesmo, pelo lápis, ou no PC e `git push`).
- `dados/estado_nuvem.json` guarda o que já foi avisado, para não repetir notificação.

## Rodar no PC (opcional)
1. `pip install -r requirements.txt`
2. Seu tópico do ntfy vai em `config.local.json` (`{"ntfy": {"topic": "..."}}`). Não use o `config.json` para isso.
3. `python -m cinema_classicos --teste-ntfy` confirma que o aviso chega.
4. `abrir.bat` abre `http://localhost:8765` com os botões **Buscar agora** (busca, atualiza e avisa) e
   **Testar busca** (log por cinema: salas, filmes, sessões, período; não avisa nem grava nada).
5. Linha de comando: `python -m cinema_classicos` (busca), `--dry-run` (não avisa), `--testar`, `--diagnostico`.
6. Agendar no Windows: `agendar.bat` (00:00 e 12:00). **Não use junto com a nuvem**, senão os avisos duplicam.

## Ajustes
- `movies.json`: adicione filmes e apelidos (título em inglês, sem acento etc.).
- `match_threshold` (0.88, em `config.json`): suba se vier falso positivo, desça se perder filme.

## Aviso importante
Os endereços do Ingresso.com não são documentados oficialmente e podem mudar.
Se o teste falhar, a fonte precisa de ajuste em `cinema_classicos/ingresso.py`.
