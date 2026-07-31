// ── Opsi Metode Evaluasi (Statis) ─────────────────────────────────────────────
const metodeOptions = [
    { kode: 'T',   label: 'T — Tugas'                              },
    { kode: 'P',   label: 'P — Praktikum/Proyek'                   },
    { kode: 'K',   label: 'K — Kuis'                               },
    { kode: 'ATS', label: 'ATS — Asesmen Tengah Semester'          },
    { kode: 'AAS', label: 'AAS — Asesmen Akhir Semester'           },
    { kode: 'PP',  label: 'PP — Presentasi Progres/Proyek'         },
];

// ── Render Metode Tags (multi-select per baris) ───────────────────────────────
function buildMetodeTags(m, savedMetode) {
    const selected = savedMetode ? savedMetode.split(',').map(s => s.trim()) : [];

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

    // Header and Grid Container
    container.innerHTML = `
        <div class="flex items-center justify-between mb-4">
            <div>
                <h3 class="text-base font-bold text-slate-900 dark:text-white">Rencana Mingguan</h3>
                <p class="text-xs text-slate-500 dark:text-slate-400">Klik setiap kartu untuk mengisi/edit Rencana Mingguan.</p>
            </div>
        </div>
        <div id="minggu-grid" class="grid grid-cols-2 md:grid-cols-4 gap-4"></div>
        <div id="minggu-modals"></div>
    `;

    const grid = document.getElementById('minggu-grid');
    const modalsContainer = document.getElementById('minggu-modals');

    listSemester.forEach(function (m) {
        const isExam = (m === 'ATS' || m === 'AAS');
        const saved = getSavedMingguan(m);

        const kemampuanVal = saved ? saved.kemampuan : (isExam ? 'Asesmen/Ujian ' + m : '');
        const bahanVal = saved ? saved.bahan_kajian : (isExam ? 'Materi Ujian' : '');
        const subBahanVal = saved ? saved.sub_bahan : '';
        const modalitasVal = saved ? saved.modalitas : (isExam ? 'Luring' : 'Blended Learning');
        const waktuVal = saved ? saved.waktu : '';
        const pengalamanVal = saved ? saved.pengalaman : '';
        const tpRefVal = saved ? saved.tp_ref : '';

        // Card HTML
        grid.innerHTML += `
            <div id="card-minggu-${m}" class="border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 rounded-2xl shadow-sm hover:shadow-md hover:border-blue-300 dark:hover:border-blue-700 transition-all cursor-pointer p-5 flex flex-col gap-4 relative overflow-hidden group" onclick="openWeekModal('${m}')">
                ${isExam ? '<div class="absolute top-0 right-0 w-12 h-12 bg-blue-500/10 dark:bg-blue-500/20 rounded-bl-[40px]"></div>' : ''}
                <div class="flex flex-col gap-3 items-start">
                    <span class="inline-flex items-center px-3 py-1.5 rounded-xl text-lg font-black bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-100">
                        ${isExam ? '' : 'Minggu '}${m}
                    </span>
                    <div id="status-badge-${m}"></div>
                </div>
                <div class="flex-1">
                    <p class="text-[10px] font-bold text-slate-400 uppercase mb-1">Materi / Kegiatan</p>
                    <p class="text-sm font-bold text-slate-700 dark:text-slate-200 line-clamp-3 leading-relaxed" id="card-desc-${m}">
                        ${kemampuanVal || '<span class="italic text-slate-400 font-normal">Belum diisi...</span>'}
                    </p>
                </div>
                <div class="pt-3 border-t border-slate-100 dark:border-slate-700/50 flex justify-between items-center text-slate-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    <span class="text-xs font-bold">Isi Rencana</span>
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
                </div>
            </div>
        `;

        // Modal HTML
        modalsContainer.innerHTML += `
            <div id="modal-minggu-${m}" class="fixed inset-0 z-[100] hidden bg-slate-900/50 backdrop-blur-sm items-center justify-center p-4">
                <div class="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 dark:border-slate-700" onclick="event.stopPropagation()">
                    <div class="p-5 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-800/30 rounded-t-2xl">
                        <div>
                            <h3 class="font-black text-2xl text-slate-800 dark:text-slate-100">${isExam ? m : 'Minggu ' + m}</h3>
                            <p class="text-xs text-slate-500 font-medium">Isi detail rencana pembelajaran mingguan.</p>
                        </div>
                        <button type="button" onclick="closeWeekModal('${m}')" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-all">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                        </button>
                    </div>
                    <div class="p-6 overflow-y-auto flex-1 bg-white dark:bg-slate-900">
                        <div class="grid grid-cols-1 md:grid-cols-4 gap-5">
                            <input type="hidden" name="minggu_ke[]" value="${m}">
                            
                            <div class="md:col-span-4 bg-blue-50 dark:bg-blue-900/20 p-4 rounded-xl border border-blue-100 dark:border-blue-800/50">
                                <label class="block text-xs font-black text-blue-800 dark:text-blue-300 uppercase mb-2 tracking-wide">TP Ref (Referensi Tujuan Pembelajaran)</label>
                                <div id="tp-box-${m}" class="flex flex-wrap gap-1 mb-2">
                                    <span class="text-xs text-blue-500/70 italic font-medium">Memuat TP...</span>
                                </div>
                                <input type="hidden" name="tp_ref[]" id="hidden-tp-${m}" value="${tpRefVal}">
                            </div>

                            <div class="md:col-span-2 flex flex-col gap-5">
                                <div>
                                    <label class="block text-[11px] font-bold text-slate-500 uppercase mb-1.5">Kemampuan Akhir</label>
                                    <input type="text" name="kemampuan[]" id="kemampuan-${m}" value="${kemampuanVal}" oninput="updateCardDesc('${m}', this.value)"
                                        class="w-full p-3 border rounded-xl text-sm focus:ring-2 focus:ring-blue-400 outline-none dark:bg-slate-800 dark:border-slate-700 bg-slate-50 dark:text-slate-200 transition-shadow">
                                </div>
                                <div class="flex-1 flex flex-col">
                                    <label class="block text-[11px] font-bold text-slate-500 uppercase mb-1.5">Pokok Bahasan</label>
                                    <textarea name="bahan_kajian[]" id="bahan_kajian-${m}"
                                        class="w-full flex-1 p-3 border rounded-xl text-sm focus:ring-2 focus:ring-blue-400 outline-none dark:bg-slate-800 dark:border-slate-700 bg-slate-50 dark:text-slate-200 transition-shadow resize-none min-h-[120px]">${bahanVal}</textarea>
                                </div>
                            </div>

                            <div class="md:col-span-2 space-y-5">
                                <div>
                                    <label class="block text-[11px] font-bold text-slate-500 uppercase mb-1.5">Modalitas & Metode</label>
                                    <textarea name="modalitas[]" id="modalitas-${m}" rows="2"
                                        class="w-full p-3 border rounded-xl text-sm focus:ring-2 focus:ring-blue-400 outline-none dark:bg-slate-800 dark:border-slate-700 bg-slate-50 dark:text-slate-200 transition-shadow">${modalitasVal}</textarea>
                                </div>
                                <div>
                                    <label class="block text-[11px] font-bold text-slate-500 uppercase mb-1.5">Pengalaman Belajar</label>
                                    <textarea name="pengalaman[]" id="pengalaman-${m}" rows="3"
                                        class="w-full p-3 border rounded-xl text-sm focus:ring-2 focus:ring-blue-400 outline-none dark:bg-slate-800 dark:border-slate-700 bg-slate-50 dark:text-slate-200 transition-shadow">${pengalamanVal}</textarea>
                                </div>
                                <div>
                                    <label class="block text-[11px] font-bold text-slate-500 uppercase mb-1.5">Estimasi Waktu</label>
                                    <input type="text" name="waktu[]" id="waktu-${m}" value="${waktuVal}" placeholder="1x2x50'"
                                        class="w-full p-3 border rounded-xl text-sm focus:ring-2 focus:ring-blue-400 outline-none dark:bg-slate-800 dark:border-slate-700 bg-slate-50 dark:text-slate-200 transition-shadow">
                                </div>
                            </div>

                            <div class="md:col-span-4 mt-2">
                                <label class="block text-[11px] font-bold text-blue-500 uppercase mb-1.5">Sub Pokok Bahasan</label>
                                <textarea name="sub_bahan[]" id="sub_bahan-${m}" rows="4"
                                    onfocus="initBullet(this)" onkeydown="handleBullet(event,this)"
                                    class="w-full p-3 border border-blue-200 dark:border-blue-800/50 rounded-xl text-sm focus:ring-2 focus:ring-blue-400 outline-none dark:bg-slate-800 bg-blue-50/30 dark:bg-blue-900/10 dark:text-slate-200 transition-shadow">${subBahanVal}</textarea>
                            </div>
                        </div>
                    </div>
                    <div class="p-5 border-t border-slate-100 dark:border-slate-800 flex justify-end gap-3 bg-slate-50/50 dark:bg-slate-800/30 rounded-b-2xl">
                        <button type="button" onclick="closeWeekModal('${m}')" class="px-5 py-2.5 rounded-xl bg-blue-600 text-white font-bold hover:bg-blue-700 transition-all shadow-md shadow-blue-500/20">Simpan & Tutup</button>
                    </div>
                </div>
            </div>
        `;
    });

    syncTPSelections();
    
    // Initial check for week statuses
    listSemester.forEach(m => {
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
};

window.closeWeekModal = function(m) {
    const modal = document.getElementById(`modal-minggu-${m}`);
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        checkWeekStatus(m);
    }
};

window.checkWeekStatus = function(m) {
    const kemampuan = document.getElementById(`kemampuan-${m}`)?.value.trim() || '';
    const bahan_kajian = document.getElementById(`bahan_kajian-${m}`)?.value.trim() || '';
    const modalitas = document.getElementById(`modalitas-${m}`)?.value.trim() || '';
    const pengalaman = document.getElementById(`pengalaman-${m}`)?.value.trim() || '';
    const waktu = document.getElementById(`waktu-${m}`)?.value.trim() || '';
    
    const isSelesai = kemampuan && bahan_kajian && modalitas && pengalaman && waktu;
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
    const descEl = document.getElementById(`card-desc-${m}`);
    if (descEl) {
        descEl.innerHTML = val ? val : '<span class="italic text-slate-400 font-normal">Belum diisi...</span>';
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
        const metodeVal     = saved ? saved.metode     : (isExam ? (m === 'ATS' ? 'ATS' : 'AAS') : '');
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