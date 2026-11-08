// Widget multi-select prasyarat mata kuliah (dipakai di Katalog MK & SLP).
// opts.searchUrl : endpoint matakuliah.search
// opts.params    : fungsi opsional -> object query tambahan (prodi_id, kurikulum, exclude_id)
function createPrasyaratWidget(searchInputId, dropId, tagsId, hiddenId, opts = {}) {
    const searchInput = document.getElementById(searchInputId);
    const drop = document.getElementById(dropId);
    const tagsContainer = document.getElementById(tagsId);
    const hiddenInput = document.getElementById(hiddenId);
    if (!searchInput || !drop || !tagsContainer || !hiddenInput) return null;

    const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));

    let selectedList = [];
    let timer;

    function syncHidden() {
        hiddenInput.value = selectedList.join(', ');
    }

    function renderTags() {
        tagsContainer.innerHTML = '';
        if (!selectedList.length) {
            tagsContainer.innerHTML = '<span class="text-xs text-slate-400 italic">Belum ada prasyarat.</span>';
            return;
        }
        selectedList.forEach((val, idx) => {
            const chip = document.createElement('span');
            chip.className = 'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold font-mono bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800';
            chip.innerHTML = `<span>${esc(val)}</span><button type="button" title="Hapus" class="hover:text-red-500 font-bold text-sm leading-none">&times;</button>`;
            chip.querySelector('button').addEventListener('click', () => {
                selectedList.splice(idx, 1);
                syncHidden();
                renderTags();
            });
            tagsContainer.appendChild(chip);
        });
    }

    function setList(arr) {
        selectedList = [...new Set((arr || []).map(s => String(s).trim()).filter(Boolean))];
        syncHidden();
        renderTags();
    }

    function add(code) {
        if (code && !selectedList.includes(code)) {
            selectedList.push(code);
            syncHidden();
            renderTags();
        }
    }

    async function runSearch() {
        const q = searchInput.value.trim();
        const params = new URLSearchParams({ q, ...(opts.params ? opts.params() : {}) });
        for (const [k, v] of [...params]) if (v === '' || v == null) params.delete(k);

        const res = await fetch(`${opts.searchUrl}?${params}`);
        const data = (await res.json()).filter(item => !selectedList.includes(item.kode));
        drop.innerHTML = '';
        if (!data.length) {
            drop.innerHTML = '<p class="px-3 py-2 text-xs text-slate-400 italic">Tidak ditemukan.</p>';
        } else {
            data.forEach(item => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'w-full text-left px-3 py-2 text-xs hover:bg-blue-50 dark:hover:bg-slate-700 border-b border-slate-100 dark:border-slate-700 last:border-0 flex items-center gap-2';
                btn.innerHTML = `<span class="font-bold font-mono text-blue-600 dark:text-blue-400 shrink-0">${esc(item.kode)}</span>
                    <span class="text-slate-700 dark:text-slate-200 truncate flex-1">${esc(item.nama)}</span>
                    ${item.semester ? `<span class="text-[10px] text-slate-400 shrink-0">Sem ${esc(item.semester)}</span>` : ''}`;
                btn.addEventListener('click', () => {
                    add(item.kode);
                    searchInput.value = '';
                    drop.classList.add('hidden');
                });
                drop.appendChild(btn);
            });
        }
        drop.classList.remove('hidden');
    }

    searchInput.addEventListener('input', () => {
        clearTimeout(timer);
        timer = setTimeout(runSearch, 200);
    });
    // Klik/fokus tanpa mengetik langsung menampilkan daftar MK yang tersedia
    searchInput.addEventListener('focus', () => {
        clearTimeout(timer);
        timer = setTimeout(runSearch, 50);
    });
    searchInput.addEventListener('keydown', e => {
        if (e.key === 'Enter') e.preventDefault();
    });

    document.addEventListener('click', e => {
        if (!searchInput.contains(e.target) && !drop.contains(e.target)) drop.classList.add('hidden');
    });

    renderTags();
    return { setList };
}
