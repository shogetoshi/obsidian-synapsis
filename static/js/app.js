let currentMode = null;
let modesData = null;

// ページ読み込み時にモード一覧を取得
async function loadModes() {
    try {
        const res = await fetch('/modes');
        const data = await res.json();
        modesData = data;

        // タブを生成
        const tabsContainer = document.getElementById('modeTabs');
        data.modes.forEach(mode => {
            const tab = document.createElement('div');
            tab.className = 'mode-tab';
            tab.onclick = () => selectMode(mode.id);
            tab.innerHTML = `
                <div class="mode-tab-name">${mode.name}</div>
                <div class="mode-tab-desc">${mode.description}</div>
            `;
            tab.dataset.modeId = mode.id;
            tabsContainer.appendChild(tab);
        });

        // デフォルトモードを選択
        selectMode(data.default_mode);
    } catch (e) {
        showMessage('モード読み込みエラー: ' + e.message, 'error');
    }
}

// モードを選択
function selectMode(modeId) {
    const mode = modesData.modes.find(m => m.id === modeId);
    if (!mode) return;

    currentMode = mode;

    // タブのアクティブ状態を更新
    document.querySelectorAll('.mode-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.modeId === modeId);
    });

    // タイトルと説明を更新
    document.getElementById('modeTitle').textContent = mode.name;
    document.getElementById('modeDescription').textContent = mode.description;

    // AI回答を非表示
    document.getElementById('aiResponse').style.display = 'none';
    document.getElementById('message').style.display = 'none';
}

// 保存のみ
async function saveContent() {
    const content = document.getElementById('content').value;
    const btn = document.getElementById('saveBtn');

    if (!content.trim()) {
        showMessage('内容を入力してください', 'error');
        return;
    }

    btn.disabled = true;
    btn.textContent = '保存中...';

    try {
        const res = await fetch('/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        const data = await res.json();

        if (res.ok) {
            let message = data.message;

            // Git push結果を追加
            if (data.git_pushed) {
                message += ' (Git push成功)';
            } else if (data.git_error) {
                message += ` (Git push失敗: ${data.git_error})`;
            }

            showMessage(message, data.git_pushed ? 'success' : 'warning');
            document.getElementById('content').value = '';
        } else {
            showMessage(data.detail || '保存に失敗しました', 'error');
        }
    } catch (e) {
        showMessage('エラー: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '保存のみ';
    }
}

// AIに質問
async function askAI() {
    const content = document.getElementById('content').value;
    const btn = document.getElementById('askAIBtn');
    const responseDiv = document.getElementById('aiResponse');
    const responseContent = document.getElementById('aiResponseContent');

    if (!content.trim()) {
        showMessage('内容を入力してください', 'error');
        return;
    }

    if (!currentMode) {
        showMessage('モードが選択されていません', 'error');
        return;
    }

    btn.disabled = true;
    btn.textContent = 'AI処理中...';
    responseDiv.style.display = 'none';

    try {
        const res = await fetch('/ask-ai', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content,
                mode_id: currentMode.id
            })
        });
        const data = await res.json();

        if (res.ok) {
            let message = data.message;

            // Git push結果を追加
            if (data.git_pushed) {
                message += ' (Git push成功)';
            } else if (data.git_error) {
                message += ` (Git push失敗: ${data.git_error})`;
            }

            showMessage(message, data.git_pushed ? 'success' : 'warning');
            responseContent.textContent = data.ai_response;
            responseDiv.style.display = 'block';
        } else {
            showMessage(data.detail || 'AI処理に失敗しました', 'error');
        }
    } catch (e) {
        showMessage('エラー: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'AIに質問';
    }
}

function showMessage(text, type) {
    const msg = document.getElementById('message');
    msg.textContent = text;
    msg.className = type;
}

// ページ読み込み時にモードを読み込む
loadModes();
