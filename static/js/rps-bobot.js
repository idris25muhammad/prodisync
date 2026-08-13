function slugifyKomponen(name) {
    return name.replace(/\s+/g, '-').replace(/\//g, '-');
}

window.addSubKomponen = function (komponen) {
    const groupId = 'group-' + slugifyKomponen(komponen);
    const container = document.getElementById(groupId);
    if (!container) return;

    const row = document.createElement('div');
    row.className = 'subkomponen-row flex flex-col md:flex-row gap-3 items-start';
    row.setAttribute('data-komponen', komponen);
    row.innerHTML = `
        <input type="hidden" name="komponen_nilai[]" value="${komponen}">

        <div class="w-full md:w-9/12">
            <textarea name="sub_komponen[]" rows="1"
                placeholder="Deskripsi sub komponen"
                class="w-full p-2 border rounded text-sm outline-none dark:bg-slate-800 dark:border-slate-600"></textarea>
        </div>

        <div class="w-full md:w-3/12 flex gap-2">
            <div class="relative flex-1">
                <input type="number" name="persentase[]" min="0" max="100" step="1" placeholder="0"
                    class="kriteria-bobot w-full p-2 pr-7 border rounded text-sm text-center outline-none dark:bg-slate-800 dark:border-slate-600">
                <span class="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-slate-400 font-bold pointer-events-none">%</span>
            </div>
            <button type="button" onclick="removeSubKomponen(this)"
                class="text-red-400 hover:text-red-600 dark:hover:text-red-400 p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30 transition-all" title="Hapus">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5">
                    <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                </svg>
            </button>
        </div>
    `;

    container.appendChild(row);
    updateKriteriaTotal();
};

window.removeSubKomponen = function (btn) {
    const row = btn.closest('.subkomponen-row');
    if (!row) return;

    const container = row.parentElement;
    row.remove();

    if (container && container.querySelectorAll('.subkomponen-row').length === 0) {
        const komponen = container.id.replace('group-', '').replace(/-/g, ' ');
        addSubKomponen(komponen);
    }

    updateKriteriaTotal();
};

window.updateKriteriaTotal = function () {
    const rows = document.querySelectorAll('.subkomponen-row');
    const totalEl = document.getElementById('kriteria-total');
    const pblTotalEl = document.getElementById('kriteria-pbl-total');
    const warningEl = document.getElementById('kriteria-warning');
    const submitBtns = document.querySelectorAll('.btn-submit-rps');
    const pblChecked = document.querySelector('input[name="is_pbl"]:checked');
    const isPbl = pblChecked && pblChecked.value === 'ya';

    let total = 0;
    let totalPblKomponen = 0;

    rows.forEach(function (row) {
        const komponenInput = row.querySelector('input[name="komponen_nilai[]"]');
        const bobotInput = row.querySelector('.kriteria-bobot');

        if (!komponenInput || !bobotInput) return;

        let val = parseFloat(bobotInput.value);
        if (isNaN(val)) val = 0;

        if (val < 0) val = 0;
        if (val > 100) val = 100;

        if (bobotInput.value !== '') {
            bobotInput.value = val;
        }

        total += val;

        const komponen = komponenInput.value.trim();
        if (komponen === 'Partisipatif' || komponen === 'Proyek' || komponen === 'Hasil Proyek') {
            totalPblKomponen += val;
        }
    });

    if (totalEl) {
        totalEl.textContent = total + '%';
        totalEl.classList.remove(
            'text-blue-600', 'dark:text-blue-400',
            'text-red-600', 'dark:text-red-400',
            'text-emerald-600', 'dark:text-emerald-400'
        );
    }

    if (pblTotalEl) {
        pblTotalEl.textContent = totalPblKomponen + '%';
        pblTotalEl.classList.remove(
            'text-slate-700', 'dark:text-slate-200',
            'text-red-600', 'dark:text-red-400',
            'text-emerald-600', 'dark:text-emerald-400'
        );
        pblTotalEl.classList.add('text-slate-700', 'dark:text-slate-200');
    }

    if (!warningEl || !submitBtns.length) return;

    warningEl.classList.remove(
        'text-slate-500', 'dark:text-slate-400',
        'text-red-600', 'dark:text-red-400',
        'text-emerald-600', 'dark:text-emerald-400'
    );

    submitBtns.forEach(function (btn) {
        btn.disabled = false;
        btn.classList.remove('opacity-50', 'cursor-not-allowed');
    });
    syncSubmitSlpNote();

    if (total > 100) {
        if (totalEl) totalEl.classList.add('text-red-600', 'dark:text-red-400');
        warningEl.classList.add('text-red-600', 'dark:text-red-400');
        warningEl.textContent = 'Total bobot melebihi 100%. Kurangi bobot sebelum menyimpan.';
        submitBtns.forEach(function (btn) {
            btn.disabled = true;
            btn.classList.add('opacity-50', 'cursor-not-allowed');
        });
        syncSubmitSlpNote();
        return;
    }

    if (total < 100) {
        if (totalEl) totalEl.classList.add('text-blue-600', 'dark:text-blue-400');
        warningEl.classList.add('text-slate-500', 'dark:text-slate-400');
        warningEl.textContent = 'Sisa bobot: ' + (100 - total) + '%. Total harus tepat 100%.';
        submitBtns.forEach(function (btn) {
            btn.disabled = true;
            btn.classList.add('opacity-50', 'cursor-not-allowed');
        });
        syncSubmitSlpNote();
        return;
    }

    if (isPbl && totalPblKomponen < 50) {
        if (totalEl) totalEl.classList.add('text-emerald-600', 'dark:text-emerald-400');
        if (pblTotalEl) {
            pblTotalEl.classList.remove('text-slate-700', 'dark:text-slate-200');
            pblTotalEl.classList.add('text-red-600', 'dark:text-red-400');
        }
        warningEl.classList.add('text-red-600', 'dark:text-red-400');
        warningEl.textContent = 'Karena matakuliah PBL, total Partisipatif + Proyek minimal 50%.';
        submitBtns.forEach(function (btn) {
            btn.disabled = true;
            btn.classList.add('opacity-50', 'cursor-not-allowed');
        });
        syncSubmitSlpNote();
        return;
    }

    if (totalEl) totalEl.classList.add('text-emerald-600', 'dark:text-emerald-400');
    if (isPbl && pblTotalEl) {
        pblTotalEl.classList.remove('text-slate-700', 'dark:text-slate-200');
        pblTotalEl.classList.add('text-emerald-600', 'dark:text-emerald-400');
    }
    warningEl.classList.add('text-emerald-600', 'dark:text-emerald-400');
    warningEl.textContent = isPbl
        ? 'Valid. Total 100% dan syarat PBL terpenuhi.'
        : 'Valid. Total bobot sudah pas 100%.';
    syncSubmitSlpNote();
};

function syncSubmitSlpNote() {
    const note = document.getElementById('submit-slp-note');
    if (!note) return;
    const btn = document.querySelector('.btn-submit-rps');
    if (btn && btn.disabled) {
        note.classList.remove('hidden');
    } else {
        note.classList.add('hidden');
    }
}

window.isKriteriaValid = function () {
    const rows = document.querySelectorAll('.subkomponen-row');
    const pblChecked = document.querySelector('input[name="is_pbl"]:checked');
    const isPbl = pblChecked && pblChecked.value === 'ya';

    let total = 0;
    let totalPblKomponen = 0;

    rows.forEach(function (row) {
        const komponenInput = row.querySelector('input[name="komponen_nilai[]"]');
        const bobotInput = row.querySelector('.kriteria-bobot');
        if (!komponenInput || !bobotInput) return;

        const val = parseFloat(bobotInput.value);
        const bobot = isNaN(val) ? 0 : val;
        total += bobot;

        const k = komponenInput.value.trim();
        if (k === 'Partisipatif' || k === 'Proyek' || k === 'Hasil Proyek') {
            totalPblKomponen += bobot;
        }
    });

    if (total !== 100) return false;
    if (isPbl && totalPblKomponen < 50) return false;
    return true;
};

document.addEventListener('input', function (e) {
    if (
        e.target.matches('.kriteria-bobot') ||
        e.target.matches('input[name="is_pbl"]')
    ) {
        updateKriteriaTotal();
    }
});

document.addEventListener('change', function (e) {
    if (e.target.matches('input[name="is_pbl"]')) {
        updateKriteriaTotal();
    }
});

document.addEventListener('DOMContentLoaded', function () {
    updateKriteriaTotal();

    const form = document.getElementById('rps-editor-form');
    if (!form) return;

    form.addEventListener('submit', function (e) {
        const rows = document.querySelectorAll('.subkomponen-row');
        const pblChecked = document.querySelector('input[name="is_pbl"]:checked');
        const isPbl = pblChecked && pblChecked.value === 'ya';

        let total = 0;
        let totalPblKomponen = 0;

        rows.forEach(function (row) {
            const komponenInput = row.querySelector('input[name="komponen_nilai[]"]');
            const bobotInput = row.querySelector('.kriteria-bobot');

            if (!komponenInput || !bobotInput) return;

            const val = parseFloat(bobotInput.value);
            const bobot = isNaN(val) ? 0 : val;

            total += bobot;

            if (
                komponenInput.value.trim() === 'Partisipatif' ||
                komponenInput.value.trim() === 'Proyek' ||
                komponenInput.value.trim() === 'Hasil Proyek'
            ) {
                totalPblKomponen += bobot;
            }
        });

        if (total !== 100) {
            e.preventDefault();
            alert('Total bobot penilaian harus tepat 100%. Sekarang totalnya ' + total + '%.');
            return;
        }

        if (isPbl && totalPblKomponen < 50) {
            e.preventDefault();
            alert('Karena ini matakuliah PBL, total bobot Partisipatif + Proyek minimal 50%. Sekarang totalnya ' + totalPblKomponen + '%.');
        }
    });
});