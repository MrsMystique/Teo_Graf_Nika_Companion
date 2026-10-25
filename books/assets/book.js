(() => {
  const prompt = document.getElementById('prompt-text');
  async function copy(text, button) {
    const box = button.closest('.takeaway, .appendix');
    const status = box?.querySelector('.copy-status');
    try {
      let done = false;
      if (navigator.clipboard && window.isSecureContext) {
        try { await navigator.clipboard.writeText(text); done = true; } catch { /* File mode fallback below. */ }
      }
      if (!done) {
        const area = document.createElement('textarea');
        area.value = text; area.style.position = 'fixed'; area.style.opacity = '0';
        document.body.append(area); area.select(); done = document.execCommand('copy'); area.remove(); button.focus();
      }
      if (!done) throw new Error('Copy unavailable');
      if (status) status.textContent = 'Готово. Вставь в новый ИИ-чат, затем напиши свой вопрос.';
    } catch {
      if (status) status.textContent = 'Браузер не разрешил копирование. Скачай TXT или открой полный текст ниже и скопируй вручную.';
    }
  }
  document.querySelectorAll('[data-copy-prompt]').forEach(button => button.addEventListener('click', () => copy(prompt.textContent, button)));
  const quotes = {
    theo: 'Здесь известен результат НОК, а n нужно найти. Число n должно делить 25. Все натуральные решения: 1, 5, 25. Для каждого НОК с 25 равен 25; других решений нет, поскольку других натуральных делителей у 25 нет.',
    graf: 'Хочется записать n = 25 и объявить дело закрытым. Но слово «все» переживает такие торжественные заявления. Если 25 — общее кратное, оно делится на n. Значит, берём все натуральные делители 25: 1, 5, 25. Каждый подходит; других делителей нет. В мою рукопись: НОК(n; 25) = 25 тогда и только тогда, когда n — натуральный делитель 25.'
  };
  document.querySelectorAll('[data-voice]').forEach(button => button.addEventListener('click', () => {
    document.querySelectorAll('[data-voice]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    document.querySelector('.voice-quote').textContent = quotes[button.dataset.voice];
  }));
  let opened = [];
  addEventListener('beforeprint', () => { opened = [...document.querySelectorAll('details:not([open])')]; opened.forEach(item => item.open = true); });
  addEventListener('afterprint', () => { opened.forEach(item => item.open = false); });
})();
