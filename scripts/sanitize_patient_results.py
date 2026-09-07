from pathlib import Path
import re

p = Path("index.html")
s = p.read_text(encoding="utf-8")
original = s

qmatch = re.search(r"(\s*const questionsData = \{.*?\n\s*\};)", s, re.S)
assert qmatch, "questionsData block not found"
questions_before = qmatch.group(1)

replacements = {
    "<title>RAC‑5TR: Rastreio Autoaplicável Clínico – Versão DSM‑5‑TR</title>": "<title>Panorama do seu momento emocional</title>",
    '<meta property="og:site_name" content="RAC‑5TR">': '<meta property="og:site_name" content="Plataforma Terapêutica Richelmy Murta">',
    '<meta property="og:title" content="RAC‑5TR: Rastreio Autoaplicável Clínico – Versão DSM‑5‑TR">': '<meta property="og:title" content="Panorama do seu momento emocional">',
    '<meta name="twitter:title" content="RAC‑5TR: Rastreio Autoaplicável Clínico">': '<meta name="twitter:title" content="Panorama do seu momento emocional">',
    '<p>Informe seu nome e a data, depois leia cada questão e selecione a resposta que melhor descreve sua experiência (0 = Nunca, 1 = Raramente, 2 = Frequentemente, 3 = Sempre). Ao terminar, clique em <strong>"Corrigir"</strong> para visualizar seu resultado. <em>O resultado final será avaliado pelo psicólogo.</em></p>': '<p>Informe seus dados, leia cada questão e selecione a resposta que melhor descreve sua experiência (0 = Nunca, 1 = Raramente, 2 = Frequentemente, 3 = Sempre). A conclusão só será confirmada após o registro técnico das respostas.</p>',
    '<h3 id="block1Title">Ansiedade Social (TAS)</h3>': '<h3 id="block1Title">Bloco 1</h3>',
    '<h3 id="block2Title">Depressão (TDM)</h3>': '<h3 id="block2Title">Bloco 2</h3>',
    '<h3 id="block3Title">Ansiedade Generalizada (TAG)</h3>': '<h3 id="block3Title">Bloco 3</h3>',
    '<h3 id="block4Title">Personalidade Evitativa (TPE)</h3>': '<h3 id="block4Title">Bloco 4</h3>',
    '<h3 id="block5Title">Obsessivo‑Compulsivo (TOC)</h3>': '<h3 id="block5Title">Bloco 5</h3>',
    '<h3 id="block6Title">Autoestima / Desvalor</h3>': '<h3 id="block6Title">Bloco 6</h3>',
    '<h3 id="block7Title">Afetivo Bipolar (TAB)</h3>': '<h3 id="block7Title">Bloco 7</h3>',
    '<button type="button" id="btnCorrigir">Corrigir</button>': '<button type="button" id="btnConcluir">Concluir rastreio</button>',
}
for old, new in replacements.items():
    if old in s:
        s = s.replace(old, new, 1)

s, n = re.subn(
    r'\n\s*<section id="results".*?</section>\s*\n\s*</main>',
    "\n\t</main>",
    s,
    count=1,
    flags=re.S,
)
assert n == 1, "patient results section not found exactly once"

s = re.sub(r"\n\s*/\* Resultados \*/.*?\nfooter\s*\{", "\nfooter {", s, count=1, flags=re.S)

scorer_start = s.find("\n\t\tconst level = score =>")
script_end = s.find("\n\t</script>", scorer_start)
assert scorer_start >= 0 and script_end > scorer_start, "legacy scorer runtime not found"

safe_runtime = r'''

		document.addEventListener('DOMContentLoaded', () => {
		  Object.keys(questionsData).forEach((key, i) => {
		    document.getElementById(`questions${i+1}`).innerHTML =
		      questionsData[key].map((q, j) => `
		        <div class="question">
		          <p>${j+1}. ${q}</p>
		          <div class="options">
		            <label><input type="radio" name="${key}_${j+1}" value="0" required>0</label>
		            <label><input type="radio" name="${key}_${j+1}" value="1">1</label>
		            <label><input type="radio" name="${key}_${j+1}" value="2">2</label>
		            <label><input type="radio" name="${key}_${j+1}" value="3">3</label>
		          </div>
		        </div>
		      `).join('');
		  });
		  document.getElementById('darkModeToggle')
		    .addEventListener('click', () => document.body.classList.toggle('dark'));
		});'''
s = s[:scorer_start] + safe_runtime + s[script_end:]

qmatch_after = re.search(r"(\s*const questionsData = \{.*?\n\s*\};)", s, re.S)
assert qmatch_after and qmatch_after.group(1) == questions_before, "clinical items changed during sanitization"

for token in (
    "Quadro Clínico Mais Provável",
    "clinicalSummary",
    'id="results"',
    "resultsTitle",
    "const level = score",
    "score <= 10",
    "score <= 20",
    "btnCorrigir",
    "s/30*100",
):
    assert token not in s, f"legacy result token remains: {token}"

assert "Concluir rastreio" in s
assert "screening-uniformity-v1.js" in s
assert s != original
p.write_text(s, encoding="utf-8")
