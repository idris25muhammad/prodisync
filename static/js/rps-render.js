// ── Helper HTML Escape ────────────────────────────────────────────────────────
function esc(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// ── Daftar 16 Minggu Standar RPS ──────────────────────────────────────────────
// (listSemester, getSavedMingguan, getSavedEvaluasi sudah dideklarasikan di rps-core.js)
const weekListP1 = ['1', '2', '3', '4', '5', '6', '7'];
const weekListP2 = ['8', '9', '10', '11', '12', '13', '14'];

// ── Opsi Metode Evaluasi (Statis) ─────────────────────────────────────────────
const metodeOptions = [
    { kode: 'A', label: 'A — Assignment' },
    { kode: 'Q', label: 'Q — Quiz' },
    { kode: 'MSE', label: 'MSE — Mid-Semester Exam' },
    { kode: 'FSE', label: 'FSE — Final-Semester Exam' },
    { kode: 'P', label: 'P — Practice/Project' },
    { kode: 'PP', label: 'PP — Project Presentation, Demo or Team meeting' },
];

const metodeCodeMap = { T: 'A', K: 'Q', ATS: 'MSE', AAS: 'FSE', P: 'P', PP: 'PP' };

function normalizeMetodeCode(raw) {
    const k = (raw || '').trim().toUpperCase();
    return metodeCodeMap[k] || k;
}

// ── Render Metode Tags (multi-select per baris Tab 4) ─────────────────────────
function buildMetodeTags(m, savedMetode) {
    const selected = savedMetode
        ? savedMetode.split(',').map(s => normalizeMetodeCode(s)).filter(Boolean)
        : [];

    return `
    <div class="eval-metode-wrapper relative">
        <div id="metode-tags-${m}" class="flex flex-wrap gap-1 min-h-[28px] p-1 border rounded dark:border-slate-600 bg-white dark:bg-slate-700 cursor-pointer"
            onclick="toggleMetodeDropdown('${m}')">
            <span class="text-[10px] text-slate-400 italic metode-placeholder ${selected.length ? 'hidden' : ''}">Pilih metode...</span>
        </div>
        <input type="hidden" name="eval_metode[]" id="eval-hidden-metode-${m}" value="${esc(selected.join(', '))}">

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
    document.querySelectorAll('[id^="metode-dropdown-"]').forEach(el => {
        if (el.id !== `metode-dropdown-${m}`) el.classList.add('hidden');
    });
    const target = document.getElementById(`metode-dropdown-${m}`);
    if (target) target.classList.toggle('hidden');
}

function updateMetodeTags(m) {
    const dropdown = document.getElementById(`metode-dropdown-${m}`);
    const tagsBox = document.getElementById(`metode-tags-${m}`);
    const hiddenInput = document.getElementById(`eval-hidden-metode-${m}`);
    if (!dropdown || !tagsBox || !hiddenInput) return;

    const placeholder = tagsBox.querySelector('.metode-placeholder');
    const checked = Array.from(dropdown.querySelectorAll('input:checked')).map(cb => cb.value);
    hiddenInput.value = checked.join(', ');

    const existingTags = tagsBox.querySelectorAll('.metode-tag');
    existingTags.forEach(t => t.remove());

    if (checked.length === 0) {
        if (placeholder) placeholder.classList.remove('hidden');
    } else {
        if (placeholder) placeholder.classList.add('hidden');
        checked.forEach(kode => {
            const tag = document.createElement('span');
            tag.className = 'metode-tag inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300';
            tag.innerHTML = `${kode} <button type="button" onclick="removeMetodeTag('${m}','${kode}')" class="hover:text-red-500 font-black leading-none">&times;</button>`;
            tagsBox.insertBefore(tag, placeholder);
        });
    }
}

function removeMetodeTag(m, kode) {
    const dropdown = document.getElementById(`metode-dropdown-${m}`);
    if (!dropdown) return;
    const cb = dropdown.querySelector(`input[value="${kode}"]`);
    if (cb) { cb.checked = false; }
    updateMetodeTags(m);
}

document.addEventListener('click', e => {
    if (!e.target.closest('.eval-metode-wrapper')) {
        document.querySelectorAll('[id^="metode-dropdown-"]').forEach(el => el.classList.add('hidden'));
    }
});

// ── Render Kotak Gantt Chart (Per Minggu 1-7 & 8-14) ──────────────────────────
function renderWeekCard(m) {
    const title = `Minggu ${m}`;

    return `
    <div id="week-card-${m}" onclick="openWeekModal('${m}')"
        class="group relative flex flex-col justify-between p-3 rounded-2xl border border-slate-200 dark:border-slate-700/80 bg-white dark:bg-slate-800/90 shadow-sm hover:shadow-md hover:-translate-y-1 transition-all duration-200 cursor-pointer select-none min-h-[142px]">
        
        <!-- Header: Minggu -->
        <div class="flex items-center justify-between w-full mb-1">
            <span class="text-xs font-black text-slate-800 dark:text-slate-100">
                ${esc(title)}
            </span>
        </div>

        <!-- Center: Icon Status & Label (Sudah / Belum) -->
        <div class="flex flex-col items-center justify-center my-1">
            <div id="status-icon-${m}" class="w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 mb-1">
                <!-- Icon disuntikkan oleh checkWeekStatus -->
            </div>
            <div id="status-label-${m}" class="text-[10px] font-bold tracking-tight">
                <!-- Label disuntikkan oleh checkWeekStatus -->
            </div>
        </div>

        <!-- Bottom: Preview CLO & Pokok Bahasan -->
        <div class="w-full pt-1.5 border-t border-slate-100 dark:border-slate-700/50 flex flex-col items-center text-center">
            <div id="preview-clo-${m}" class="flex flex-wrap justify-center gap-0.5 mb-1 max-h-5 overflow-hidden"></div>
            <div id="preview-desc-${m}" class="text-[10px] text-slate-500 dark:text-slate-400 truncate w-full px-0.5">
                <span class="italic text-slate-400">Klik untuk isi</span>
            </div>
        </div>
    </div>`;
}

// ── Render Card Ujian Full Baris (ATS & AAS) ──────────────────────────────────
function renderFullWidthExamCard(m) {
    const isATS = (m === 'ATS');
    const examName = isATS ? 'Asesmen Tengah Semester (ATS)' : 'Asesmen Akhir Semester (AAS)';
    const examDesc = isATS
        ? 'Evaluasi capaian pembelajaran paruh pertama (Minggu 1 s.d. 7)'
        : 'Evaluasi capaian pembelajaran akhir semester (Minggu 8 s.d. 14 & komprehensif)';

    const borderClass = isATS
        ? 'border-amber-300 dark:border-amber-700/80 bg-gradient-to-r from-amber-50/70 via-white to-amber-50/30 dark:from-amber-950/20 dark:via-slate-800/90 dark:to-slate-800/80 hover:border-amber-400'
        : 'border-indigo-300 dark:border-indigo-700/80 bg-gradient-to-r from-indigo-50/70 via-white to-indigo-50/30 dark:from-indigo-950/20 dark:via-slate-800/90 dark:to-slate-800/80 hover:border-indigo-400';

    const badgeClass = isATS
        ? 'bg-amber-500 text-white shadow-amber-500/20'
        : 'bg-indigo-600 text-white shadow-indigo-600/20';

    const tagClass = isATS
        ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300'
        : 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-300';

    return `
    <div id="week-card-${m}" onclick="openWeekModal('${m}')"
        class="group relative flex flex-col md:flex-row items-stretch md:items-center justify-between p-4 rounded-2xl border ${borderClass} shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 cursor-pointer select-none gap-4">
        
        <!-- Left: Badge & Title -->
        <div class="flex items-center gap-3.5 min-w-[280px]">
            <div class="w-12 h-12 rounded-2xl ${badgeClass} font-black text-sm flex items-center justify-center shrink-0 shadow-md">
                ${m}
            </div>
            <div>
                <div class="flex items-center gap-2">
                    <h4 class="text-sm font-black text-slate-800 dark:text-slate-100">${esc(examName)}</h4>
                    <span class="text-[9px] font-black px-2 py-0.5 rounded-full ${tagClass} uppercase tracking-wider">Ujian</span>
                </div>
                <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">${esc(examDesc)}</p>
            </div>
        </div>

        <!-- Middle: Preview CLO & Topic -->
        <div class="flex-1 border-t md:border-t-0 md:border-l md:border-r border-slate-200/80 dark:border-slate-700/70 pt-2 md:pt-0 md:px-5 flex flex-col justify-center">
            <div id="preview-clo-${m}" class="flex flex-wrap gap-1 mb-1"></div>
            <div id="preview-desc-${m}" class="text-xs text-slate-600 dark:text-slate-300 truncate max-w-xl">
                <span class="italic text-slate-400">Klik untuk mengisi materi/pokok bahasan ujian</span>
            </div>
        </div>

        <!-- Right: Status Icon & Action -->
        <div class="flex items-center justify-between md:justify-end gap-3.5 shrink-0">
            <div class="flex items-center gap-2">
                <div id="status-icon-${m}" class="w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200">
                    <!-- Icon disuntikkan oleh checkWeekStatus -->
                </div>
                <div id="status-label-${m}" class="text-xs font-bold tracking-tight">
                    <!-- Label disuntikkan oleh checkWeekStatus -->
                </div>
            </div>
            <button type="button" class="px-3.5 py-1.5 rounded-xl bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 group-hover:border-blue-400 text-xs font-bold text-slate-700 dark:text-slate-200 shadow-sm group-hover:text-blue-600 transition-colors">
                Detail
            </button>
        </div>
    </div>`;
}

// ── Render Modal Pengisian (Per Minggu) ───────────────────────────────────────
function renderWeekModal(m) {
    const isExam = (m === 'ATS' || m === 'AAS');
    const saved = getSavedMingguan(m);

    const kemampuanVal = saved?.kemampuan || '';
    const bahanVal = saved?.bahan_kajian || '';
    const subBahanVal = saved?.sub_bahan || '';
    const modalitasVal = saved?.modalitas || (isExam ? '' : "Blended learning: lecture, lab practice, group discussion, PBL (CDIO)");
    const waktuVal = saved?.waktu || (isExam ? '' : "PB 2x50'; PT 2x60'; BM 2x60'; Lab Practice 1x170'");
    const pengalamanVal = saved?.pengalaman || '';
    const tpRefVal = saved?.tp_ref || '';

    const modalTitle = isExam
        ? (m === 'ATS' ? 'Asesmen Tengah Semester (ATS)' : 'Asesmen Akhir Semester (AAS)')
        : 'Rencana Pembelajaran Minggu ' + m;

    return `
    <div id="modal-minggu-${m}" class="fixed inset-0 z-[100] hidden bg-slate-900/60 backdrop-blur-sm items-center justify-center p-4">
        <div class="bg-white dark:bg-slate-900 rounded-3xl w-full max-w-3xl max-h-[92vh] flex flex-col shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden" onclick="event.stopPropagation()">
            
            <!-- Modal Header -->
            <div class="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/80 dark:bg-slate-800/40">
                <div class="flex items-center gap-3">
                    <span class="w-10 h-10 rounded-2xl ${isExam ? (m === 'ATS' ? 'bg-amber-500' : 'bg-indigo-600') : 'bg-blue-600'} text-white flex items-center justify-center font-black text-sm shadow-md">
                        ${isExam ? m : m}
                    </span>
                    <div>
                        <h3 class="font-black text-xl text-slate-800 dark:text-slate-100">${esc(modalTitle)}</h3>
                        <p class="text-xs text-slate-500 font-medium">Lengkapi pokok bahasan, referensi CLO, dan metode pembelajaran.</p>
                    </div>
                </div>
                <button type="button" onclick="closeWeekModal('${m}')"
                    class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-all">
                    <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Modal Body -->
            <div class="p-6 overflow-y-auto flex-1 space-y-5">
                <input type="hidden" name="minggu_ke[]" value="${esc(m)}">
                <input type="hidden" name="kemampuan[]" id="kemampuan-${m}" value="${esc(kemampuanVal)}">
                <input type="hidden" name="pengalaman[]" id="pengalaman-${m}" value="${esc(pengalamanVal)}">

                <!-- Fitur Copy dari Minggu Lain -->
                <div class="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-50 dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-700">
                    <div class="flex items-center gap-2">
                        <svg class="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        <span class="text-xs font-bold text-slate-700 dark:text-slate-300">Salin dari Minggu Lain:</span>
                    </div>
                    <select onchange="copyFromWeek('${m}', this.value); this.value='';"
                        class="text-xs font-semibold px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-blue-500 shadow-sm cursor-pointer">
                        <option value="">-- Pilih minggu sumber --</option>
                        ${listSemester.filter(w => w !== m).map(w => {
        const isWExam = (w === 'ATS' || w === 'AAS');
        const label = isWExam ? w : 'Minggu ' + w;
        return `<option value="${w}">Salin dari ${label}</option>`;
    }).join('')}
                    </select>
                </div>

                <!-- CLO Selection -->
                <div class="bg-blue-50/60 dark:bg-blue-900/20 p-4 rounded-2xl border border-blue-100 dark:border-blue-800/50">
                    <label class="block text-xs font-black text-blue-800 dark:text-blue-300 uppercase mb-2 tracking-wide">
                        CLO Ref (Course Learning Outcomes)
                    </label>
                    <div id="tp-box-${m}" class="flex flex-wrap gap-1.5 mb-1.5">
                        <span class="text-xs text-blue-500/70 italic font-medium">Memuat CLO...</span>
                    </div>
                    <input type="hidden" name="tp_ref[]" id="hidden-tp-${m}" value="${esc(tpRefVal)}">
                </div>

                <!-- Pokok Bahasan -->
                <div>
                    <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 uppercase mb-1.5">
                        Pokok Bahasan (Bahan Kajian) <span class="text-red-500">*</span>
                    </label>
                    <textarea name="bahan_kajian[]" id="bahan_kajian-${m}"
                        oninput="onFieldInput('${m}')"
                        placeholder="Tuliskan materi atau pokok bahasan perkuliahan..."
                        class="w-full p-3.5 border rounded-2xl text-sm focus:ring-2 focus:ring-blue-500 outline-none dark:bg-slate-800 dark:border-slate-700 bg-slate-50 dark:text-slate-200 transition-shadow resize-none min-h-[95px]">${esc(bahanVal)}</textarea>
                </div>

                <!-- Sub Pokok Bahasan -->
                <div>
                    <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 uppercase mb-1.5">
                        Sub Pokok Bahasan
                    </label>
                    <textarea name="sub_bahan[]" id="sub_bahan-${m}" rows="3"
                        onfocus="initNumbered(this)" onkeydown="handleNumbered(event,this)"
                        oninput="onFieldInput('${m}')"
                        placeholder="1. Sub bahasan materi&#10;2. Sub bahasan materi"
                        class="w-full p-3.5 border border-blue-200/80 dark:border-blue-800/50 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500 outline-none dark:bg-slate-800 bg-blue-50/20 dark:bg-blue-900/10 dark:text-slate-200 transition-shadow">${esc(subBahanVal)}</textarea>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <!-- Modalitas -->
                    <div>
                        <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 uppercase mb-1.5">Learning Method</label>
                        <textarea name="modalitas[]" id="modalitas-${m}" rows="2"
                            oninput="onFieldInput('${m}')"
                            class="w-full p-3 border rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none dark:bg-slate-800 dark:border-slate-700 bg-slate-50 dark:text-slate-200 transition-shadow">${esc(modalitasVal)}</textarea>
                    </div>

                    <!-- Waktu -->
                    <div>
                        <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 uppercase mb-1.5">Time</label>
                        <textarea name="waktu[]" id="waktu-${m}" rows="2"
                            oninput="onFieldInput('${m}')"
                            class="w-full p-3 border rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none dark:bg-slate-800 dark:border-slate-700 bg-slate-50 dark:text-slate-200 transition-shadow">${esc(waktuVal)}</textarea>
                    </div>
                </div>
            </div>

            <!-- Modal Footer -->
            <div class="px-6 py-4 border-t border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/80 dark:bg-slate-800/40">
                <span class="text-xs text-slate-400">Data otomatis terhubung ke Tab Rencana Evaluasi.</span>
                <div class="flex gap-2">
                    <button type="button" onclick="closeWeekModal('${m}')"
                        class="px-5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 font-bold text-xs text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all">
                        Tutup
                    </button>
                    <button type="button" onclick="saveWeekModal('${m}')"
                        class="px-5 py-2.5 rounded-xl bg-blue-600 text-white font-bold text-xs hover:bg-blue-700 transition-all shadow-md shadow-blue-500/20">
                        Simpan &amp; Terapkan
                    </button>
                </div>
            </div>
        </div>
    </div>`;
}

// ── Render Rencana Mingguan (Tab 3: Gantt Chart View) ─────────────────────────
function renderRencanaMingguan() {
    const container = document.getElementById('minggu-container');
    if (!container) return;

    let p1Cards = '';
    let p2Cards = '';
    let modalsHtml = '';

    weekListP1.forEach(m => {
        p1Cards += renderWeekCard(m);
    });

    weekListP2.forEach(m => {
        p2Cards += renderWeekCard(m);
    });

    listSemester.forEach(m => {
        modalsHtml += renderWeekModal(m);
    });

    container.innerHTML = `
        <!-- Quick Legend -->
        <div class="flex items-center justify-between pb-1">
            <span class="text-xs font-bold text-slate-500 uppercase tracking-wide">Alur Pembelajaran Mingguan</span>
            <div class="flex items-center gap-4 text-xs">
                <div class="flex items-center gap-1.5">
                    <span class="w-3.5 h-3.5 rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-400 flex items-center justify-center text-[10px] font-bold">✓</span>
                    <span class="text-slate-600 dark:text-slate-300 font-medium">Sudah Diisi</span>
                </div>
                <div class="flex items-center gap-1.5">
                    <span class="w-3.5 h-3.5 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-500 flex items-center justify-center text-[10px] font-bold">○</span>
                    <span class="text-slate-600 dark:text-slate-300 font-medium">Belum Diisi</span>
                </div>
            </div>
        </div>

        <!-- 1. Minggu 1 s.d. 7 -->
        <div class="space-y-2.5">
            <div class="flex items-center gap-2.5">
                <span class="px-2.5 py-0.5 rounded-md bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 font-black text-xs uppercase tracking-wide">Minggu 1 – 7</span>
                <span class="text-xs font-semibold text-slate-500">Perkuliahan Paruh Pertama</span>
                <div class="h-px bg-slate-200 dark:bg-slate-700 flex-1"></div>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
                ${p1Cards}
            </div>
        </div>

        <!-- 2. ATS (Full Baris) -->
        <div class="pt-1">
            ${renderFullWidthExamCard('ATS')}
        </div>

        <!-- 3. Minggu 8 s.d. 14 -->
        <div class="space-y-2.5 pt-2">
            <div class="flex items-center gap-2.5">
                <span class="px-2.5 py-0.5 rounded-md bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 font-black text-xs uppercase tracking-wide">Minggu 8 – 14</span>
                <span class="text-xs font-semibold text-slate-500">Perkuliahan Paruh Kedua</span>
                <div class="h-px bg-slate-200 dark:bg-slate-700 flex-1"></div>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
                ${p2Cards}
            </div>
        </div>

        <!-- 4. AAS (Full Baris) -->
        <div class="pt-1">
            ${renderFullWidthExamCard('AAS')}
        </div>

        <!-- Modals Container -->
        <div id="minggu-modals">${modalsHtml}</div>`;

    if (typeof syncTPSelections === 'function') {
        syncTPSelections();
    }

    listSemester.forEach(m => {
        checkWeekStatus(m);
    });
}

// ── Status Evaluator & UI Updater ─────────────────────────────────────────────
window.checkWeekStatus = function (m) {
    const isExam = (m === 'ATS' || m === 'AAS');
    const bahan_kajian = document.getElementById(`bahan_kajian-${m}`)?.value.trim() || '';
    const tpRef = document.getElementById(`hidden-tp-${m}`)?.value.trim() || '';
    const modalitas = document.getElementById(`modalitas-${m}`)?.value.trim() || '';
    const waktu = document.getElementById(`waktu-${m}`)?.value.trim() || '';

    // Terisi jika pokok bahasan atau referensi CLO diisi
    const isFilled = isExam
        ? Boolean(bahan_kajian || tpRef)
        : Boolean(bahan_kajian);

    const isComplete = Boolean(bahan_kajian && tpRef && modalitas && (isExam || waktu));

    const iconEl = document.getElementById(`status-icon-${m}`);
    const labelEl = document.getElementById(`status-label-${m}`);
    const cardEl = document.getElementById(`week-card-${m}`);
    const previewDesc = document.getElementById(`preview-desc-${m}`);
    const previewClo = document.getElementById(`preview-clo-${m}`);

    if (iconEl && labelEl) {
        if (isFilled) {
            iconEl.className = 'w-9 h-9 rounded-full flex items-center justify-center transition-all duration-200 mb-1 bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-400 ring-2 ring-emerald-500/20 shadow-sm';
            iconEl.innerHTML = `
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>`;
            labelEl.className = 'text-[11px] font-bold tracking-tight text-emerald-600 dark:text-emerald-400';
            labelEl.textContent = isComplete ? 'Sudah Lengkap' : 'Sudah Diisi';

            if (cardEl && !isExam) {
                cardEl.classList.remove('border-slate-200', 'dark:border-slate-700/80');
                cardEl.classList.add('border-emerald-300', 'dark:border-emerald-800/80');
            }
        } else {
            iconEl.className = 'w-9 h-9 rounded-full flex items-center justify-center transition-all duration-200 mb-1 bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500 border border-slate-200 dark:border-slate-700';
            iconEl.innerHTML = `
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="7" stroke-dasharray="3 3"/>
                </svg>`;
            labelEl.className = 'text-[11px] font-medium tracking-tight text-slate-400 dark:text-slate-500';
            labelEl.textContent = 'Belum Diisi';

            if (cardEl && !isExam) {
                cardEl.classList.remove('border-emerald-300', 'dark:border-emerald-800/80');
                cardEl.classList.add('border-slate-200', 'dark:border-slate-700/80');
            }
        }
    }

    if (previewDesc) {
        if (bahan_kajian) {
            previewDesc.textContent = bahan_kajian;
            previewDesc.title = bahan_kajian;
            previewDesc.classList.remove('italic', 'text-slate-400');
            previewDesc.classList.add('text-slate-600', 'dark:text-slate-300');
        } else {
            previewDesc.textContent = 'Klik untuk isi';
            previewDesc.title = '';
            previewDesc.classList.add('italic', 'text-slate-400');
            previewDesc.classList.remove('text-slate-600', 'dark:text-slate-300');
        }
    }

    if (previewClo) {
        if (tpRef) {
            const chips = tpRef.split(',').map(s => s.trim()).filter(Boolean);
            previewClo.innerHTML = chips.map(c =>
                `<span class="inline-flex items-center text-[9px] font-bold px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800/40">${esc(c)}</span>`
            ).join('');
        } else {
            previewClo.innerHTML = '';
        }
    }

    updateOverallProgress();
};

function updateOverallProgress() {
    let filledCount = 0;
    listSemester.forEach(m => {
        const isExam = (m === 'ATS' || m === 'AAS');
        const bahan = document.getElementById(`bahan_kajian-${m}`)?.value.trim() || '';
        const tp = document.getElementById(`hidden-tp-${m}`)?.value.trim() || '';
        if (isExam ? (bahan || tp) : Boolean(bahan)) {
            filledCount++;
        }
    });

    const progressEl = document.getElementById('weekly-plan-progress');
    if (progressEl) {
        const pct = Math.round((filledCount / listSemester.length) * 100);
        progressEl.innerHTML = `
            <span class="w-2 h-2 rounded-full ${filledCount === listSemester.length ? 'bg-emerald-500' : 'bg-blue-500 animate-pulse'}"></span>
            <span>${filledCount} / ${listSemester.length} Minggu Diisi (${pct}%)</span>`;
    }
}

window.onFieldInput = function (m) {
    checkWeekStatus(m);
};

// ── Modal Actions ─────────────────────────────────────────────────────────────
window.openWeekModal = function (m) {
    const modal = document.getElementById(`modal-minggu-${m}`);
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
};

window.closeWeekModal = function (m) {
    const modal = document.getElementById(`modal-minggu-${m}`);
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        checkWeekStatus(m);
    }
};

window.saveWeekModal = function (m) {
    closeWeekModal(m);
    if (typeof showToast === 'function') {
        const title = (m === 'ATS' || m === 'AAS') ? m : `Minggu ${m}`;
        showToast(`Detail ${title} disimpan`, 'success');
    }
};

window.copyFromWeek = function (targetWeek, sourceWeek) {
    if (!sourceWeek) return;

    // Baca nilai dari form minggu sumber
    const srcBahan = document.getElementById(`bahan_kajian-${sourceWeek}`)?.value || '';
    const srcSub = document.getElementById(`sub_bahan-${sourceWeek}`)?.value || '';
    const srcMod = document.getElementById(`modalitas-${sourceWeek}`)?.value || '';
    const srcWaktu = document.getElementById(`waktu-${sourceWeek}`)?.value || '';
    const srcTp = document.getElementById(`hidden-tp-${sourceWeek}`)?.value || '';
    const srcKemp = document.getElementById(`kemampuan-${sourceWeek}`)?.value || '';
    const srcPeng = document.getElementById(`pengalaman-${sourceWeek}`)?.value || '';

    // Terapkan ke elemen form minggu target
    const targetBahan = document.getElementById(`bahan_kajian-${targetWeek}`);
    if (targetBahan) targetBahan.value = srcBahan;

    const targetSub = document.getElementById(`sub_bahan-${targetWeek}`);
    if (targetSub) targetSub.value = srcSub;

    const targetMod = document.getElementById(`modalitas-${targetWeek}`);
    if (targetMod) targetMod.value = srcMod;

    const targetWaktu = document.getElementById(`waktu-${targetWeek}`);
    if (targetWaktu) targetWaktu.value = srcWaktu;

    const targetKemp = document.getElementById(`kemampuan-${targetWeek}`);
    if (targetKemp) targetKemp.value = srcKemp;

    const targetPeng = document.getElementById(`pengalaman-${targetWeek}`);
    if (targetPeng) targetPeng.value = srcPeng;

    const targetTp = document.getElementById(`hidden-tp-${targetWeek}`);
    if (targetTp) targetTp.value = srcTp;

    // Sinkronkan checkbox pilihan CLO di modal
    const tpCount = (typeof getCloList === 'function') ? getCloList().length : 0;
    if (tpCount > 0 && typeof updateCheckboxGroup === 'function') {
        updateCheckboxGroup(targetWeek, 'mingguan', tpCount);
        updateCheckboxGroup(targetWeek, 'evaluasi', tpCount);
    }

    // Perbarui status card dan badge
    if (typeof checkWeekStatus === 'function') {
        checkWeekStatus(targetWeek);
    }

    if (typeof showToast === 'function') {
        const srcLabel = (sourceWeek === 'ATS' || sourceWeek === 'AAS') ? sourceWeek : 'Minggu ' + sourceWeek;
        const tgtLabel = (targetWeek === 'ATS' || targetWeek === 'AAS') ? targetWeek : 'Minggu ' + targetWeek;
        showToast(`Data dari ${srcLabel} disalin ke ${tgtLabel}`, 'success');
    }
};

// ── Render Kotak Gantt Chart Evaluasi (Per Minggu 1-7 & 8-14) ─────────────────
function renderEvalCard(m) {
    const title = `Minggu ${m}`;

    return `
    <div id="eval-card-${m}" onclick="openEvalModal('${m}')"
        class="group relative flex flex-col justify-between p-3 rounded-2xl border border-slate-200 dark:border-slate-700/80 bg-white dark:bg-slate-800/90 shadow-sm hover:shadow-md hover:-translate-y-1 transition-all duration-200 cursor-pointer select-none min-h-[142px]">
        
        <!-- Header: Minggu -->
        <div class="flex items-center justify-between w-full mb-1">
            <span class="text-xs font-black text-slate-800 dark:text-slate-100">
                ${esc(title)}
            </span>
        </div>

        <!-- Center: Icon Status & Label (Sudah / Belum) -->
        <div class="flex flex-col items-center justify-center my-1">
            <div id="eval-status-icon-${m}" class="w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 mb-1">
                <!-- Icon disuntikkan oleh checkEvalStatus -->
            </div>
            <div id="eval-status-label-${m}" class="text-[10px] font-bold tracking-tight">
                <!-- Label disuntikkan oleh checkEvalStatus -->
            </div>
        </div>

        <!-- Bottom: Preview Metode & CLO -->
        <div class="w-full pt-1.5 border-t border-slate-100 dark:border-slate-700/50 flex flex-col items-center text-center">
            <div id="eval-preview-metode-${m}" class="flex flex-wrap justify-center gap-1 mb-1 max-h-5 overflow-hidden"></div>
            <div id="eval-preview-clo-${m}" class="text-[10px] text-slate-500 dark:text-slate-400 truncate w-full px-0.5">
                <span class="italic text-slate-400">Klik untuk atur</span>
            </div>
        </div>
    </div>`;
}

// ── Render Card Ujian Evaluasi Full Baris (ATS & AAS) ─────────────────────────
function renderFullWidthEvalExamCard(m) {
    const isATS = (m === 'ATS');
    const examName = isATS ? 'Asesmen Tengah Semester (ATS)' : 'Asesmen Akhir Semester (AAS)';
    const examDesc = isATS
        ? 'Pemetaan metode evaluasi asesmen capaian paruh pertama (Minggu 1 s.d. 7)'
        : 'Pemetaan metode evaluasi asesmen capaian akhir semester (Minggu 8 s.d. 14 & komprehensif)';

    const borderClass = isATS
        ? 'border-amber-300 dark:border-amber-700/80 bg-gradient-to-r from-amber-50/70 via-white to-amber-50/30 dark:from-amber-950/20 dark:via-slate-800/90 dark:to-slate-800/80 hover:border-amber-400'
        : 'border-indigo-300 dark:border-indigo-700/80 bg-gradient-to-r from-indigo-50/70 via-white to-indigo-50/30 dark:from-indigo-950/20 dark:via-slate-800/90 dark:to-slate-800/80 hover:border-indigo-400';

    const badgeClass = isATS
        ? 'bg-amber-500 text-white shadow-amber-500/20'
        : 'bg-indigo-600 text-white shadow-indigo-600/20';

    const tagClass = isATS
        ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300'
        : 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-300';

    return `
    <div id="eval-card-${m}" onclick="openEvalModal('${m}')"
        class="group relative flex flex-col md:flex-row items-stretch md:items-center justify-between p-4 rounded-2xl border ${borderClass} shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 cursor-pointer select-none gap-4">
        
        <!-- Left: Badge & Title -->
        <div class="flex items-center gap-3.5 min-w-[280px]">
            <div class="w-12 h-12 rounded-2xl ${badgeClass} font-black text-sm flex items-center justify-center shrink-0 shadow-md">
                ${m}
            </div>
            <div>
                <div class="flex items-center gap-2">
                    <h4 class="text-sm font-black text-slate-800 dark:text-slate-100">${esc(examName)}</h4>
                    <span class="text-[9px] font-black px-2 py-0.5 rounded-full ${tagClass} uppercase tracking-wider">Ujian</span>
                </div>
                <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">${esc(examDesc)}</p>
            </div>
        </div>

        <!-- Middle: Preview CLO & Metode -->
        <div class="flex-1 border-t md:border-t-0 md:border-l md:border-r border-slate-200/80 dark:border-slate-700/70 pt-2 md:pt-0 md:px-5 flex flex-col justify-center">
            <div class="flex items-center gap-2 mb-1">
                <span class="text-[10px] font-bold text-slate-400 uppercase">Metode Asesmen:</span>
                <div id="eval-preview-metode-${m}" class="flex flex-wrap gap-1"></div>
            </div>
            <div id="eval-preview-clo-${m}" class="text-xs text-slate-600 dark:text-slate-300 truncate max-w-xl">
                <span class="italic text-slate-400">Klik untuk mengatur metode penilaian ujian</span>
            </div>
        </div>

        <!-- Right: Status Icon & Action -->
        <div class="flex items-center justify-between md:justify-end gap-3.5 shrink-0">
            <div class="flex items-center gap-2">
                <div id="eval-status-icon-${m}" class="w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200">
                    <!-- Icon disuntikkan oleh checkEvalStatus -->
                </div>
                <div id="eval-status-label-${m}" class="text-xs font-bold tracking-tight">
                    <!-- Label disuntikkan oleh checkEvalStatus -->
                </div>
            </div>
            <button type="button" class="px-3.5 py-1.5 rounded-xl bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 group-hover:border-blue-400 text-xs font-bold text-slate-700 dark:text-slate-200 shadow-sm group-hover:text-blue-600 transition-colors">
                Detail
            </button>
        </div>
    </div>`;
}

// ── Render Modal Evaluasi (Per Minggu) ────────────────────────────────────────
function renderEvalModal(m) {
    const isExam = (m === 'ATS' || m === 'AAS');
    const saved = getSavedEvaluasi(m);

    const tpVal = saved ? saved.tp : '';
    const metodeVal = saved ? saved.metode : '';
    const keteranganVal = saved ? saved.keterangan : '';

    const selectedCodes = metodeVal
        ? metodeVal.split(',').map(s => normalizeMetodeCode(s)).filter(Boolean)
        : [];

    const modalTitle = isExam
        ? (m === 'ATS' ? 'Metode Evaluasi — Asesmen Tengah Semester (ATS)' : 'Metode Evaluasi — Asesmen Akhir Semester (AAS)')
        : 'Metode Evaluasi — Minggu ' + m;

    return `
    <div id="modal-eval-${m}" class="fixed inset-0 z-[100] hidden bg-slate-900/60 backdrop-blur-sm items-center justify-center p-4">
        <div class="bg-white dark:bg-slate-900 rounded-3xl w-full max-w-2xl max-h-[92vh] flex flex-col shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden" onclick="event.stopPropagation()">
            
            <!-- Modal Header -->
            <div class="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/80 dark:bg-slate-800/40">
                <div class="flex items-center gap-3">
                    <span class="w-10 h-10 rounded-2xl ${isExam ? (m === 'ATS' ? 'bg-amber-500' : 'bg-indigo-600') : 'bg-blue-600'} text-white flex items-center justify-center font-black text-sm shadow-md">
                        ${isExam ? m : m}
                    </span>
                    <div>
                        <h3 class="font-black text-xl text-slate-800 dark:text-slate-100">${esc(modalTitle)}</h3>
                        <p class="text-xs text-slate-500 font-medium">Pilih metode evaluasi asesmen yang diterapkan pada minggu ini.</p>
                    </div>
                </div>
                <button type="button" onclick="closeEvalModal('${m}')"
                    class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-all">
                    <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Modal Body -->
            <div class="p-6 overflow-y-auto flex-1 space-y-5">
                <input type="hidden" name="eval_minggu[]" value="${esc(m)}">
                <input type="hidden" name="eval_tp[]" id="eval-hidden-tp-${m}" value="${esc(tpVal)}">
                <input type="hidden" name="eval_metode[]" id="eval-hidden-metode-${m}" value="${esc(selectedCodes.join(', '))}">
                <input type="hidden" name="eval_keterangan[]" value="${esc(keteranganVal)}">

                <!-- Salin dari Minggu Lain -->
                <div class="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-50 dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-700">
                    <div class="flex items-center gap-2">
                        <svg class="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        <span class="text-xs font-bold text-slate-700 dark:text-slate-300">Salin dari Minggu Lain:</span>
                    </div>
                    <select onchange="copyEvalFromWeek('${m}', this.value); this.value='';"
                        class="text-xs font-semibold px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-blue-500 shadow-sm cursor-pointer">
                        <option value="">-- Pilih minggu sumber --</option>
                        ${listSemester.filter(w => w !== m).map(w => {
        const isWExam = (w === 'ATS' || w === 'AAS');
        const label = isWExam ? w : 'Minggu ' + w;
        return `<option value="${w}">Salin metode dari ${label}</option>`;
    }).join('')}
                    </select>
                </div>

                <!-- CLO Terpetakan (Readonly synced from Weekly Course Plan) -->
                <div class="bg-blue-50/60 dark:bg-blue-900/20 p-4 rounded-2xl border border-blue-100 dark:border-blue-800/50">
                    <label class="block text-xs font-black text-blue-800 dark:text-blue-300 uppercase mb-2 tracking-wide">
                        CLO Ref Terpetakan
                    </label>
                    <div id="eval-tp-box-${m}" class="flex flex-wrap gap-1.5 mb-1">
                        <span class="text-xs text-blue-500/70 italic font-medium">Memuat CLO...</span>
                    </div>
                    <p class="text-[11px] text-slate-400 mt-1">CLO terhubung otomatis dengan pilihan Course Learning Outcomes di Weekly Course Plan.</p>
                </div>

                <!-- Opsi Metode Evaluasi (Multi Checkbox) -->
                <div>
                    <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 uppercase mb-2">
                        Pilihan Metode Asesmen (Centang semua yang berlaku)
                    </label>
                    <div id="eval-checkbox-group-${m}" class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        ${metodeOptions.map(opt => `
                        <label class="flex items-center gap-3 p-3 rounded-2xl border border-slate-200 dark:border-slate-700 hover:border-blue-400 dark:hover:border-blue-500 bg-white dark:bg-slate-800 cursor-pointer transition-all hover:bg-blue-50/30 dark:hover:bg-blue-900/20">
                            <input type="checkbox" value="${opt.kode}"
                                ${selectedCodes.includes(opt.kode) ? 'checked' : ''}
                                onchange="onEvalCheckboxChange('${m}')"
                                class="w-5 h-5 accent-blue-600 rounded cursor-pointer">
                            <div>
                                <span class="font-black text-xs text-blue-700 dark:text-blue-400 mr-1.5">${opt.kode}</span>
                                <span class="text-xs text-slate-700 dark:text-slate-200 font-medium">${opt.label.split('—')[1].trim()}</span>
                            </div>
                        </label>`).join('')}
                    </div>
                </div>
            </div>

            <!-- Modal Footer -->
            <div class="px-6 py-4 border-t border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/80 dark:bg-slate-800/40">
                <span class="text-xs text-slate-400">Pilihan metode tersimpan otomatis saat Anda menutup.</span>
                <div class="flex gap-2">
                    <button type="button" onclick="closeEvalModal('${m}')"
                        class="px-5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 font-bold text-xs text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all">
                        Tutup
                    </button>
                    <button type="button" onclick="saveEvalModal('${m}')"
                        class="px-5 py-2.5 rounded-xl bg-blue-600 text-white font-bold text-xs hover:bg-blue-700 transition-all shadow-md shadow-blue-500/20">
                        Simpan &amp; Terapkan
                    </button>
                </div>
            </div>
        </div>
    </div>`;
}

// ── Status Evaluator & UI Updater (Tab 4) ──────────────────────────────────────
window.onEvalCheckboxChange = function (m) {
    const group = document.getElementById(`eval-checkbox-group-${m}`);
    const hiddenInput = document.getElementById(`eval-hidden-metode-${m}`);
    if (!group || !hiddenInput) return;

    const checked = Array.from(group.querySelectorAll('input:checked')).map(cb => cb.value);
    hiddenInput.value = checked.join(', ');

    checkEvalStatus(m);
};

window.checkEvalStatus = function (m) {
    const isExam = (m === 'ATS' || m === 'AAS');
    const hiddenMetode = document.getElementById(`eval-hidden-metode-${m}`);
    const hiddenTp = document.getElementById(`eval-hidden-tp-${m}`);
    const metodeVal = (hiddenMetode?.value || '').trim();
    const tpVal = (hiddenTp?.value || '').trim();

    const isFilled = Boolean(metodeVal);

    const iconEl = document.getElementById(`eval-status-icon-${m}`);
    const labelEl = document.getElementById(`eval-status-label-${m}`);
    const cardEl = document.getElementById(`eval-card-${m}`);
    const previewMet = document.getElementById(`eval-preview-metode-${m}`);
    const previewClo = document.getElementById(`eval-preview-clo-${m}`);

    if (iconEl && labelEl) {
        if (isFilled) {
            iconEl.className = 'w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 mb-1 bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-400 ring-2 ring-emerald-500/20 shadow-sm';
            iconEl.innerHTML = `
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>`;
            labelEl.className = 'text-[10px] font-bold tracking-tight text-emerald-600 dark:text-emerald-400';
            labelEl.textContent = 'Sudah Diisi';

            if (cardEl && !isExam) {
                cardEl.classList.remove('border-slate-200', 'dark:border-slate-700/80');
                cardEl.classList.add('border-emerald-300', 'dark:border-emerald-800/80');
            }
        } else {
            iconEl.className = 'w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 mb-1 bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500 border border-slate-200 dark:border-slate-700';
            iconEl.innerHTML = `
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="7" stroke-dasharray="3 3"/>
                </svg>`;
            labelEl.className = 'text-[10px] font-medium tracking-tight text-slate-400 dark:text-slate-500';
            labelEl.textContent = 'Belum Diisi';

            if (cardEl && !isExam) {
                cardEl.classList.remove('border-emerald-300', 'dark:border-emerald-800/80');
                cardEl.classList.add('border-slate-200', 'dark:border-slate-700/80');
            }
        }
    }

    if (previewMet) {
        if (metodeVal) {
            const codes = metodeVal.split(',').map(s => s.trim()).filter(Boolean);
            previewMet.innerHTML = codes.map(c =>
                `<span class="inline-flex items-center text-[9px] font-black px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300 border border-blue-200 dark:border-blue-800/40">${esc(c)}</span>`
            ).join('');
        } else {
            previewMet.innerHTML = '<span class="text-[9px] text-slate-400 italic">Belum ada</span>';
        }
    }

    if (previewClo) {
        if (tpVal) {
            previewClo.textContent = tpVal;
            previewClo.title = 'CLO: ' + tpVal;
            previewClo.classList.remove('italic', 'text-slate-400');
            previewClo.classList.add('text-slate-600', 'dark:text-slate-300');
        } else {
            previewClo.textContent = 'Belum ada CLO';
            previewClo.title = '';
            previewClo.classList.add('italic', 'text-slate-400');
            previewClo.classList.remove('text-slate-600', 'dark:text-slate-300');
        }
    }

    updateOverallEvalProgress();
};

function updateOverallEvalProgress() {
    let filledCount = 0;
    listSemester.forEach(m => {
        const hiddenMetode = document.getElementById(`eval-hidden-metode-${m}`);
        if (hiddenMetode && hiddenMetode.value.trim()) {
            filledCount++;
        }
    });

    const progressEl = document.getElementById('eval-plan-progress');
    if (progressEl) {
        const pct = Math.round((filledCount / listSemester.length) * 100);
        progressEl.innerHTML = `
            <span class="w-2 h-2 rounded-full ${filledCount === listSemester.length ? 'bg-emerald-500' : 'bg-blue-500 animate-pulse'}"></span>
            <span>${filledCount} / ${listSemester.length} Minggu Diisi (${pct}%)</span>`;
    }
}

// ── Modal Actions Evaluasi ────────────────────────────────────────────────────
window.openEvalModal = function (m) {
    const modal = document.getElementById(`modal-eval-${m}`);
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
};

window.closeEvalModal = function (m) {
    const modal = document.getElementById(`modal-eval-${m}`);
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        checkEvalStatus(m);
    }
};

window.saveEvalModal = function (m) {
    closeEvalModal(m);
    if (typeof showToast === 'function') {
        const title = (m === 'ATS' || m === 'AAS') ? m : `Minggu ${m}`;
        showToast(`Metode evaluasi ${title} disimpan`, 'success');
    }
};

window.copyEvalFromWeek = function (targetWeek, sourceWeek) {
    if (!sourceWeek) return;

    const srcHidden = document.getElementById(`eval-hidden-metode-${sourceWeek}`);
    const srcMetode = srcHidden?.value || '';

    const tgtHidden = document.getElementById(`eval-hidden-metode-${targetWeek}`);
    if (tgtHidden) tgtHidden.value = srcMetode;

    // Sinkronkan checkbox di modal target
    const tgtGroup = document.getElementById(`eval-checkbox-group-${targetWeek}`);
    if (tgtGroup) {
        const codes = srcMetode.split(',').map(s => normalizeMetodeCode(s)).filter(Boolean);
        tgtGroup.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.checked = codes.includes(cb.value);
        });
    }

    checkEvalStatus(targetWeek);

    if (typeof showToast === 'function') {
        const srcLabel = (sourceWeek === 'ATS' || sourceWeek === 'AAS') ? sourceWeek : 'Minggu ' + sourceWeek;
        const tgtLabel = (targetWeek === 'ATS' || targetWeek === 'AAS') ? targetWeek : 'Minggu ' + targetWeek;
        showToast(`Metode evaluasi dari ${srcLabel} disalin ke ${tgtLabel}`, 'success');
    }
};

// ── Render Rencana Evaluasi (Tab 4: Gantt Chart View) ─────────────────────────
function renderRencanaEvaluasi() {
    const container = document.getElementById('reneval-container');
    if (!container) return;

    let p1Cards = '';
    let p2Cards = '';
    let modalsHtml = '';

    weekListP1.forEach(m => {
        p1Cards += renderEvalCard(m);
    });

    weekListP2.forEach(m => {
        p2Cards += renderEvalCard(m);
    });

    listSemester.forEach(m => {
        modalsHtml += renderEvalModal(m);
    });

    container.innerHTML = `
        <!-- Quick Legend -->
        <div class="flex items-center justify-between pb-1">
            <span class="text-xs font-bold text-slate-500 uppercase tracking-wide">Alur Evaluasi Asesmen Mingguan</span>
            <div class="flex items-center gap-4 text-xs">
                <div class="flex items-center gap-1.5">
                    <span class="w-3.5 h-3.5 rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-400 flex items-center justify-center text-[10px] font-bold">✓</span>
                    <span class="text-slate-600 dark:text-slate-300 font-medium">Sudah Diisi</span>
                </div>
                <div class="flex items-center gap-1.5">
                    <span class="w-3.5 h-3.5 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-500 flex items-center justify-center text-[10px] font-bold">○</span>
                    <span class="text-slate-600 dark:text-slate-300 font-medium">Belum Diisi</span>
                </div>
            </div>
        </div>

        <!-- 1. Minggu 1 s.d. 7 -->
        <div class="space-y-2.5">
            <div class="flex items-center gap-2.5">
                <span class="px-2.5 py-0.5 rounded-md bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 font-black text-xs uppercase tracking-wide">Minggu 1 – 7</span>
                <span class="text-xs font-semibold text-slate-500">Evaluasi Asesmen Paruh Pertama</span>
                <div class="h-px bg-slate-200 dark:bg-slate-700 flex-1"></div>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
                ${p1Cards}
            </div>
        </div>

        <!-- 2. ATS (Full Baris) -->
        <div class="pt-1">
            ${renderFullWidthEvalExamCard('ATS')}
        </div>

        <!-- 3. Minggu 8 s.d. 14 -->
        <div class="space-y-2.5 pt-2">
            <div class="flex items-center gap-2.5">
                <span class="px-2.5 py-0.5 rounded-md bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 font-black text-xs uppercase tracking-wide">Minggu 8 – 14</span>
                <span class="text-xs font-semibold text-slate-500">Evaluasi Asesmen Paruh Kedua</span>
                <div class="h-px bg-slate-200 dark:bg-slate-700 flex-1"></div>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
                ${p2Cards}
            </div>
        </div>

        <!-- 4. AAS (Full Baris) -->
        <div class="pt-1">
            ${renderFullWidthEvalExamCard('AAS')}
        </div>

        <!-- Modals Container -->
        <div id="eval-modals">${modalsHtml}</div>`;

    if (typeof syncTPSelections === 'function') {
        syncTPSelections();
    }

    listSemester.forEach(m => {
        checkEvalStatus(m);
    });
}

// Export ke window agar dapat dipanggil dari rps-core.js
window.renderRencanaMingguan = renderRencanaMingguan;
window.renderRencanaEvaluasi = renderRencanaEvaluasi;

// ── Init ──────────────────────────────────────────────────────────────────────
function initRpsRender() {
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
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRpsRender);
} else {
    initRpsRender();
}

if (typeof window !== 'undefined' && window.addEventListener) {
    window.addEventListener('load', function () {
        const mc = document.getElementById('minggu-container');
        if (mc && !mc.innerHTML.trim()) {
            initRpsRender();
        }
    });
}
