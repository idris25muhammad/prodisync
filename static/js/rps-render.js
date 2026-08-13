// ── Opsi Metode Evaluasi (Statis) ─────────────────────────────────────────────
// Label baru (IABEE-style). 'kode' adalah value yang disimpan; label lama dipetakan
// otomatis oleh backend (T→A, K→Q, ATS→MSE, AAS→FSE) saat render ulang.
const metodeOptions = [
    { kode: 'A',   label: 'A — Assignment'                          },
    { kode: 'Q',   label: 'Q — Quiz'                                },
    { kode: 'MSE', label: 'MSE — Mid-Semester Exam'                 },
    { kode: 'FSE', label: 'FSE — Final-Semester Exam'               },
    { kode: 'P',   label: 'P — Practice/Project'                    },
    { kode: 'PP',  label: 'PP — Project Presentation, Demo or Team meeting' },
];

// Pemetaan kode lama → baru utk menampilkan data tersimpan dengan benar
const metodeCodeMap = { T: 'A', K: 'Q', ATS: 'MSE', AAS: 'FSE', P: 'P', PP: 'PP' };

function normalizeMetodeCode(raw) {
    const k = (raw || '').trim().toUpperCase();
    return metodeCodeMap[k] || k;
}

// ── Render Metode Tags (multi-select per baris) ───────────────────────────────
function buildMetodeTags(m, savedMetode) {
    const selected = savedMetode
        ? savedMetode.split(',').map(s => normalizeMetodeCode(s)).filter(Boolean)
        : [];

    const optionsHtml = metodeOptions.map(opt => `
        <option value="${opt.kode}" ${selected.includes(opt.kode) ? 'selected' : ''}>
            ${opt.label}
        </option>`).join('');

    return `
    <div class="eval-metode-wrapper relative">
        <div id="metode-tags-${m}" class="flex flex-wrap gap-1 min-h-[28px] p-1 border rounded dark:border-slate-600 bg-white dark:bg-slate-700 cursor-pointer"
            onclick="toggleMetodeDropdown('${m}')">
            <span class="text-[10px] text-slate-400 italic metode-placeholder ${selected.length ? 'hidden' : ''}">Pilih metode...</span>
        </div>
        <input type="hidden" name="eval_metode[]" id="eval-hidden-metode-${m}" value="${selected.join(', ')}">

        <div id="metode-dropdown-${m}"
            class="hidden absolute z-50 mt-1 w-64 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-xl shadow-xl p-2 space-y-1">
            ${metodeOptions.map(opt => `
            <label class="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/30 cursor-pointer text-sm transition-colors">
                <input type="checkbox" value="${opt.kode}"
                    ${selected.includes(opt.kode) ? 'checked' : ''}
                    onchange="updateMetodeTags('${m}')"
                    class="accent-blue-600">
                <span class="font-semibold text-blue-700 dark:text-blue-400 w-8 shrink-0">${opt.kode}</span>
                <span class="text-slate-600 dark:text-slate-300 text-xs">${opt.label.split('—')[1].trim()}</span>
            </label>`).join('')}
        </div>
    </div>`;
}

function toggleMetodeDropdown(m) {
    // Tutup semua dropdown lain dulu
    document.querySelectorAll('[id^="metode-dropdown-"]').forEach(el => {
        if (el.id !== `metode-dropdown-${m}`) el.classList.add('hidden');
    });
    document.getElementById(`metode-dropdown-${m}`).classList.toggle('hidden');
}

function updateMetodeTags(m) {
    const dropdown    = document.getElementById(`metode-dropdown-${m}`);
    const tagsBox     = document.getElementById(`metode-tags-${m}`);
    const hiddenInput = document.getElementById(`eval-hidden-metode-${m}`);
    const placeholder = tagsBox.querySelector('.metode-placeholder');

    const checked = Array.from(dropdown.querySelectorAll('input:checked')).map(cb => cb.value);
    hiddenInput.value = checked.join(', ');

    // Render tags
    const existingTags = tagsBox.querySelectorAll('.metode-tag');
    existingTags.forEach(t => t.remove());

    if (checked.length === 0) {
        placeholder?.classList.remove('hidden');
    } else {
        placeholder?.classList.add('hidden');
        checked.forEach(kode => {
            const tag = document.createElement('span');
            tag.className = 'metode-tag inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300';
            tag.innerHTML = `${kode} <button type="button" onclick="removeMetodeTag('${m}','${kode}')" class="hover:text-red-500 font-black leading-none">×</button>`;
            tagsBox.insertBefore(tag, placeholder);
        });
    }
}

function removeMetodeTag(m, kode) {
    const dropdown = document.getElementById(`metode-dropdown-${m}`);
    const cb = dropdown.querySelector(`input[value="${kode}"]`);
    if (cb) { cb.checked = false; }
    updateMetodeTags(m);
}

// Klik di luar dropdown → tutup
document.addEventListener('click', e => {
    if (!e.target.closest('.eval-metode-wrapper')) {
        document.querySelectorAll('[id^="metode-dropdown-"]').forEach(el => el.classList.add('hidden'));
    }
});

function renderRencanaMingguan() {
    const container = document.getElementById('minggu-container');
    if (!container) return;

    var tableRows = '';
    var modalsHtml = '';

    listSemester.forEach(function (m) {
        var isExam = (m === 'ATS' || m === 'AAS');
        var saved = getSavedMingguan(m);

        var kemampuanVal = saved ? saved.kemampuan : (isExam ? 'Asesmen/Ujian ' + m : '');
        var bahanVal = saved ? saved.bahan_kajian : (isExam ? 'Materi Ujian' : '');
        var subBahanVal = saved ? saved.sub_bahan : '';
        var modalitasVal = saved ? saved.modalitas : (isExam ? 'Luring' : "Blended learning: lecture, lab practice, group discussion, PBL (CDIO)");
        var waktuVal = saved ? saved.waktu : (isExam ? '' : "PB 2x50'; PT 2x60'; BM 2x60'; Practicum 1x170'");
        var pengalamanVal = saved ? saved.pengalaman : '';
        var tpRefVal = saved ? saved.tp_ref : '';

        var tpBadges = '';
        if (tpRefVal) {
            var refs = tpRefVal.split(',').map(function(s) { return s.trim(); }).filter(Boolean);
            refs.forEach(function(r) {
                tpBadges += '<span class="inline-flex items-center text-[10px] font-bold bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800/50 px-1.5 py-0.5 rounded mr-0.5 mb-0.5">' + r + '</span>';
            });
        } else {
            tpBadges = '<span class="text-[10px] text-slate-400 italic">-</span>';
        }

        var bahanPreview = bahanVal
            ? bahanVal.replace(/</g, '&lt;').replace(/>/g, '&gt;').substring(0, 80) + (bahanVal.length > 80 ? '&hellip;' : '')
            : '<span class="italic text-slate-400">Belum diisi</span>';

        var modalitasPreview = modalitasVal
            ? modalitasVal.replace(/</g, '&lt;').replace(/>/g, '&gt;').substring(0, 50) + (modalitasVal.length > 50 ? '&hellip;' : '')
            : '<span class="italic text-slate-400">-</span>';

        tableRows += '<tr id="card-minggu-' + m + '" class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-blue-50/40 dark:hover:bg-blue-900/10 cursor-pointer transition-colors" onclick="openWeekModal(\'' + m + '\')">';
        tableRows += '<td class="px-3 py-3 text-sm font-black text-slate-800 dark:text-slate-100 whitespace-nowrap">' + (isExam ? m : 'Minggu ' + m) + '</td>';
        tableRows += '<td class="px-3 py-3"><div id="tp-table-' + m + '" class="flex flex-wrap gap-0.5">' + tpBadges + '</div></td>';
        tableRows += '<td class="px-3 py-3 text-xs text-slate-700 dark:text-slate-300 leading-relaxed max-w-[260px]" id="card-desc-' + m + '">' + bahanPreview + '</td>';
        tableRows += '<td class="px-3 py-3 text-xs text-slate-600 dark:text-slate-400 leading-relaxed max-w-[180px]" id="card-modalitas-' + m + '">' + modalitasPreview + '</td>';
        tableRows += '<td class="px-3 py-3 whitespace-nowrap"><div id="status-badge-' + m + '"></div></td>';
        tableRows += '</tr>';

        modalsHtml += '<div id="modal-minggu-' + m + '" class="fixed inset-0 z-[100] hidden bg-slate-900/50 backdrop-blur-sm items-center justify-center p-4">';
        modalsHtml += '<div class="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 dark:border-slate-700" onclick="event.stopPropagation()">';
        modalsHtml += '<div class="p-5 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-800/30 rounded-t-2xl">';
        modalsHtml += '<div><h3 class="font-black text-2xl text-slate-800 dark:text-slate-100">' + (isExam ? m : 'Minggu ' + m) + '</h3><p class="text-xs text-slate-500 font-medium">Isi detail rencana pembelajaran mingguan.</p></div>';
        modalsHtml += '<button type="button" onclick="closeWeekModal(\'' + m + '\')" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-all"><svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg></button>';
        modalsHtml += '</div>';
        modalsHtml += '<div class="p-6 overflow-y-auto flex-1 bg-white dark:bg-slate-900">';
        modalsHtml += '<div class="space-y-5">';
        modalsHtml += '<input type="hidden" name="minggu_ke[]" value="' + m + '">';
        modalsHtml += '<input type="hidden" name="kemampuan[]" value="' + kemampuanVal + '">';
        modalsHtml += '<input type="hidden" name="pengalaman[]" value="' + pengalamanVal + '">';
        modalsHtml += '<div class="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-xl border border-blue-100 dark:border-blue-800/50">';
        modalsHtml += '<label class="block text-xs font-black text-blue-800 dark:text-blue-300 uppercase mb-2 tracking-wide">CLO Ref (Referensi Course Learning Outcomes)</label>';
        modalsHtml += '<div id="tp-box-' + m + '" class="flex flex-wrap gap-1 mb-2"><span class="text-xs text-blue-500/70 italic font-medium">Memuat CLO...</span></div>';
        modalsHtml += '<input type="hidden" name="tp_ref[]" id="hidden-tp-' + m + '" value="' + tpRefVal + '">';
        modalsHtml += '</div>';
        modalsHtml += '<div><label class="block text-[11px] font-bold text-slate-500 uppercase mb-1.5">Pokok Bahasan</label>';
        modalsHtml += '<textarea name="bahan_kajian[]" id="bahan_kajian-' + m + '" oninput="updateCardDesc(\'' + m + '\', this.value)" class="w-full p-3 border rounded-xl text-sm focus:ring-2 focus:ring-blue-400 outline-none dark:bg-slate-800 dark:border-slate-700 bg-slate-50 dark:text-slate-200 transition-shadow resize-none min-h-[100px]">' + bahanVal + '</textarea></div>';
        modalsHtml += '<div><label class="block text-[11px] font-bold text-slate-500 uppercase mb-1.5">Sub Pokok Bahasan</label>';
        modalsHtml += '<textarea name="sub_bahan[]" id="sub_bahan-' + m + '" rows="4" onfocus="initNumbered(this)" onkeydown="handleNumbered(event,this)" class="w-full p-3 border border-blue-200 dark:border-blue-800/50 rounded-xl text-sm focus:ring-2 focus:ring-blue-400 outline-none dark:bg-slate-800 bg-blue-50/30 dark:bg-blue-900/10 dark:text-slate-200 transition-shadow">' + subBahanVal + '</textarea></div>';
        modalsHtml += '<div><label class="block text-[11px] font-bold text-slate-500 uppercase mb-1.5">Learning Method</label>';
        modalsHtml += '<textarea name="modalitas[]" id="modalitas-' + m + '" rows="2" oninput="updateCardModalitas(\'' + m + '\', this.value)" class="w-full p-3 border rounded-xl text-sm focus:ring-2 focus:ring-blue-400 outline-none dark:bg-slate-800 dark:border-slate-700 bg-slate-50 dark:text-slate-200 transition-shadow">' + modalitasVal + '</textarea></div>';
        modalsHtml += '<div><label class="block text-[11px] font-bold text-slate-500 uppercase mb-1.5">Time</label>';
        modalsHtml += '<textarea name="waktu[]" id="waktu-' + m + '" rows="2" class="w-full p-3 border rounded-xl text-sm focus:ring-2 focus:ring-blue-400 outline-none dark:bg-slate-800 dark:border-slate-700 bg-slate-50 dark:text-slate-200 transition-shadow">' + waktuVal + '</textarea></div>';
        modalsHtml += '</div></div>';
        modalsHtml += '<div class="p-5 border-t border-slate-100 dark:border-slate-800 flex justify-end gap-3 bg-slate-50/50 dark:bg-slate-800/30 rounded-b-2xl">';
        modalsHtml += '<button type="button" onclick="saveWeekModal(\'' + m + '\')" class="px-5 py-2.5 rounded-xl bg-blue-600 text-white font-bold hover:bg-blue-700 transition-all shadow-md shadow-blue-500/20">Simpan & Tutup</button>';
        modalsHtml += '</div></div></div>';
    });

    container.innerHTML = '<div class="flex items-center justify-between mb-4">' +
        '<div>' +
        '<p class="text-xs text-slate-500 dark:text-slate-400">Klik baris tabel untuk mengisi/edit rencana mingguan.</p>' +
        '<p class="text-[10px] text-amber-600 dark:text-amber-400 mt-1">Pastikan CLO dan SO-PI di tab <strong>Course Learning Outcomes</strong> sudah diisi terlebih dahulu.</p></div></div>' +
        '<div class="overflow-x-auto border border-slate-200 dark:border-slate-700 rounded-xl">' +
        '<table class="w-full text-left">' +
        '<thead class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-700">' +
        '<tr>' +
        '<th class="px-3 py-2.5 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Week</th>' +
        '<th class="px-3 py-2.5 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">CLO Ref</th>' +
        '<th class="px-3 py-2.5 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Pokok Bahasan</th>' +
        '<th class="px-3 py-2.5 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Learning Method</th>' +
        '<th class="px-3 py-2.5 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Status</th>' +
        '</tr></thead>' +
        '<tbody class="divide-y divide-slate-100 dark:divide-slate-700/50">' + tableRows + '</tbody>' +
        '</table></div>' +
        '<div id="minggu-modals">' + modalsHtml + '</div>';

    syncTPSelections();

    listSemester.forEach(function(m) {
        checkWeekStatus(m);
    });
}

// ── Modal Interactions ──
window.openWeekModal = function(m) {
    const modal = document.getElementById(`modal-minggu-${m}`);
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
    ['bahan_kajian', 'modalitas', 'waktu'].forEach(function (p) {
        const el = document.getElementById(`${p}-${m}`);
        if (el) el.classList.remove('border-red-500', 'ring-1', 'ring-red-400');
    });
    const tpBox = document.getElementById(`tp-box-${m}`);
    if (tpBox) tpBox.classList.remove('border-red-500', 'ring-1', 'ring-red-400');
};

window.closeWeekModal = function(m) {
    var modal = document.getElementById('modal-minggu-' + m);
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        updateTableTpBadges(m);
        checkWeekStatus(m);
    }
};

window.saveWeekModal = function(m) {
    const fields = [
        { id: `bahan_kajian-${m}`,  label: 'Pokok Bahasan' },
        { id: `modalitas-${m}`,     label: 'Learning Method' },
        { id: `waktu-${m}`,         label: 'Time' },
        { id: `hidden-tp-${m}`,     label: 'CLO Ref', warnBorder: false },
    ];

    const empty = [];
    fields.forEach(function (f) {
        const el = document.getElementById(f.id);
        if (!el) return;
        if (!el.value.trim()) {
            empty.push(f.label);
            if (f.warnBorder !== false) {
                el.classList.add('border-red-500', 'ring-1', 'ring-red-400');
            } else {
                const tpBox = document.getElementById(`tp-box-${m}`);
                if (tpBox) tpBox.classList.add('border-red-500', 'ring-1', 'ring-red-400');
            }
        } else {
            el.classList.remove('border-red-500', 'ring-1', 'ring-red-400');
            const tpBox = document.getElementById(`tp-box-${m}`);
            if (tpBox) tpBox.classList.remove('border-red-500', 'ring-1', 'ring-red-400');
        }
    });

    if (empty.length > 0) {
        alert(`Mohon lengkapi bidang berikut sebelum menyimpan:\n• ${empty.join('\n• ')}`);
        return;
    }

    closeWeekModal(m);
};

window.checkWeekStatus = function(m) {
    const bahan_kajian = document.getElementById(`bahan_kajian-${m}`)?.value.trim() || '';
    const modalitas = document.getElementById(`modalitas-${m}`)?.value.trim() || '';
    const waktu = document.getElementById(`waktu-${m}`)?.value.trim() || '';
    const tpRef = document.getElementById(`hidden-tp-${m}`)?.value.trim() || '';
    
    const isSelesai = bahan_kajian && modalitas && waktu && tpRef;
    const badgeContainer = document.getElementById(`status-badge-${m}`);
    
    if (badgeContainer) {
        if (isSelesai) {
            badgeContainer.innerHTML = '<span class="inline-flex items-center px-2.5 py-1 rounded-lg text-[10px] font-bold bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 border border-green-200 dark:border-green-800/50">✓ Selesai</span>';
        } else {
            badgeContainer.innerHTML = '<span class="inline-flex items-center px-2.5 py-1 rounded-lg text-[10px] font-bold bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400 border border-slate-200 dark:border-slate-700">Belum Lengkap</span>';
        }
    }
};

window.updateCardDesc = function(m, val) {
    var descEl = document.getElementById('card-desc-' + m);
    if (descEl) {
        if (val) {
            var safe = val.replace(/</g, '&lt;').replace(/>/g, '&gt;');
            descEl.innerHTML = safe.substring(0, 80) + (safe.length > 80 ? '&hellip;' : '');
        } else {
            descEl.innerHTML = '<span class="italic text-slate-400">Belum diisi</span>';
        }
    }
};


window.updateTableTpBadges = function(m) {
    var hiddenTp = document.getElementById('hidden-tp-' + m);
    var tableCell = document.getElementById('tp-table-' + m);
    if (!hiddenTp || !tableCell) return;

    var tpRefVal = hiddenTp.value.trim();
    if (tpRefVal) {
        var refs = tpRefVal.split(',').map(function(s) { return s.trim(); }).filter(Boolean);
        var html = '';
        refs.forEach(function(r) {
            html += '<span class="inline-flex items-center text-[10px] font-bold bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800/50 px-1.5 py-0.5 rounded mr-0.5 mb-0.5">' + r + '</span>';
        });
        tableCell.innerHTML = html;
    } else {
        tableCell.innerHTML = '<span class="text-[10px] text-slate-400 italic">-</span>';
    }
};


// ── Render Rencana Evaluasi (Tab 4) ───────────────────────────────────────────
function renderRencanaEvaluasi() {
    const container = document.getElementById('reneval-container');
    if (!container) return;
    
    container.innerHTML = '';

    listSemester.forEach(m => {
        const isExam = (m === 'ATS' || m === 'AAS');
        const saved  = getSavedEvaluasi(m);

        const tpVal         = saved ? saved.tp         : '';
        const metodeVal     = saved ? saved.metode     : (isExam ? (m === 'ATS' ? 'MSE' : 'FSE') : '');
        const keteranganVal = saved ? saved.keterangan : '';

        const bgClass = isExam
            ? 'bg-blue-50/50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-800'
            : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700';
            
        const textClass = isExam
            ? 'text-blue-700 dark:text-blue-400 font-bold'
            : 'text-slate-700 dark:text-slate-300 font-bold';

        container.innerHTML += `
        <div class="flex gap-4 border p-4 items-center ${bgClass} rounded-xl shadow-sm transition-colors hover:border-blue-300 dark:hover:border-blue-600">
            <div class="w-1/12 text-center text-sm ${textClass} shrink-0">
                ${m}
            </div>
            <input type="hidden" name="eval_minggu[]" value="${m}">

            <div class="w-4/12 border-l border-slate-100 dark:border-slate-700 pl-4 min-h-[40px] flex items-center">
                <div id="eval-tp-box-${m}" class="flex flex-wrap gap-1">
                    <span class="text-[10px] text-slate-400 italic">Memuat...</span>
                </div>
                <input type="hidden" name="eval_tp[]" id="eval-hidden-tp-${m}" value="${tpVal}">
            </div>

            <div class="w-7/12 pl-2">
                ${buildMetodeTags(m, metodeVal)}
            </div>
            
            <!-- Hidden Keterangan (untuk mencegah error array/zip di backend backend jika ada sisa query) -->
            <input type="hidden" name="eval_keterangan[]" value="${keteranganVal}">
        </div>`;
    });

    // Render ulang tags untuk baris yang sudah ada data
    listSemester.forEach(m => {
        const saved = getSavedEvaluasi(m);
        if (saved?.metode) updateMetodeTags(m);
    });
}


// ── Init ──────────────────────────────────────────────────────────────────────
window.onload = function () {
    try {
        renderRencanaMingguan();
    } catch (err) {
        console.error('Gagal render Rencana Mingguan:', err);
    }

    try {
        renderRencanaEvaluasi();
    } catch (err) {
        console.error('Gagal render Rencana Evaluasi:', err);
    }
};