/**
 * Stock Skills WebUI - Utility Functions
 * 共通ユーティリティ関数
 */

// 数値フォーマット
function formatNumber(num, decimals = 0) {
    if (num === null || num === undefined || isNaN(num)) {
        return 'N/A';
    }
    return num.toLocaleString('ja-JP', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

// 通貨フォーマット
function formatCurrency(amount, currency = 'JPY') {
    if (amount === null || amount === undefined || isNaN(amount)) {
        return 'N/A';
    }
    return new Intl.NumberFormat('ja-JP', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

// パーセントフォーマット
function formatPercent(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) {
        return 'N/A';
    }
    return (value * 100).toFixed(decimals) + '%';
}

// 株価フォーマット
function formatPrice(price) {
    if (price === null || price === undefined || isNaN(price)) {
        return 'N/A';
    }
    return '¥' + formatNumber(price, 0);
}

// 比率フォーマット
function formatRatio(ratio, decimals = 2) {
    if (ratio === null || ratio === undefined || isNaN(ratio)) {
        return 'N/A';
    }
    return ratio.toFixed(decimals) + '倍';
}

// 色分け（損益）
function getProfitColorClass(profit) {
    if (profit > 0) return 'text-success';
    if (profit < 0) return 'text-error';
    return '';
}

// 色分け（PER）
function getPERColorClass(pe) {
    if (pe === null || pe === undefined) return '';
    if (pe < 15) return 'text-success';
    if (pe > 25) return 'text-warning';
    return '';
}

// 色分け（PBR）
function getPBRColorClass(pb) {
    if (pb === null || pb === undefined) return '';
    if (pb < 1) return 'text-success';
    if (pb > 2) return 'text-warning';
    return '';
}

// 色分け（配当利回り）
function getDividendYieldColorClass(yield_) {
    if (yield_ === null || yield_ === undefined) return '';
    if (yield_ > 3) return 'text-success';
    return '';
}

// 割安度ラベル
function getValuationLabel(score) {
    if (score === null || score === undefined) return '標準';
    if (score >= 80) return '非常に割安';
    if (score >= 60) return 'やや割安';
    if (score >= 40) return '標準';
    if (score >= 20) return 'やや割高';
    return '非常に割高';
}

// 割安度スコアカラー
function getValuationColor(score) {
    if (score === null || score === undefined) return 'bg-gray-500';
    if (score >= 80) return 'bg-success';
    if (score >= 60) return 'bg-primary';
    if (score >= 40) return 'bg-warning';
    return 'bg-error';
}

// HHI コメント
function getHHIComment(hhi) {
    if (hhi === null || hhi === undefined) {
        return 'HHI は集中度を示す指標です。2500 未満は分散、2500-5000 は中程度、5000 超は集中とされます。';
    }
    if (hhi < 2500) return '✅ 分散されたポートフォリオです';
    if (hhi < 5000) return '⚠️ 中程度の集中度です';
    return '❌ 集中度が高いです。分散を検討してください。';
}

// ローディング表示
function showLoading(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        el.innerHTML = '<div class="loading loading-spinner loading-lg"></div>';
    }
}

// エラー表示
function showError(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) {
        el.innerHTML = `
            <div class="alert alert-error">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span>${message}</span>
            </div>
        `;
    }
}

// API リクエスト（JSON）
async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    const response = await fetch(url, options);
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '不明なエラー' }));
        throw new Error(error.detail || response.statusText);
    }
    
    return response.json();
}

// フォームデータからオブジェクト
function formDataToObject(formData) {
    const obj = {};
    formData.forEach((value, key) => {
        if (key in obj) {
            if (!Array.isArray(obj[key])) {
                obj[key] = [obj[key]];
            }
            obj[key].push(value);
        } else {
            obj[key] = value;
        }
    });
    return obj;
}

// URL パラメータ取得
function getUrlParams() {
    const params = new URLSearchParams(window.location.search);
    const result = {};
    params.forEach((value, key) => {
        result[key] = value;
    });
    return result;
}

// URL パラメータ設定
function setUrlParams(params, replace = true) {
    const url = new URL(window.location.href);
    Object.keys(params).forEach(key => {
        if (params[key] !== null && params[key] !== undefined) {
            url.searchParams.set(key, params[key]);
        } else {
            url.searchParams.delete(key);
        }
    });
    
    if (replace) {
        history.replaceState({}, '', url.toString());
    } else {
        history.pushState({}, '', url.toString());
    }
}

// トースト通知
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} shadow-lg position-fixed bottom-0 right-0 m-4 z-50`;
    toast.innerHTML = `
        <span>${message}</span>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// 確認ダイアログ
async function confirmDialog(message) {
    return confirm(message);
}

// クリップボードコピー
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('クリップボードにコピーしました', 'success');
        return true;
    } catch (err) {
        showToast('コピーに失敗しました', 'error');
        return false;
    }
}

// CSV エクスポート
function exportToCSV(data, filename = 'export.csv') {
    if (!data || data.length === 0) {
        showToast('エクスポートするデータがありません', 'warning');
        return;
    }
    
    const headers = Object.keys(data[0]);
    const csv = [
        headers.join(','),
        ...data.map(row => 
            headers.map(header => 
                '"' + String(row[header]).replace(/"/g, '""') + '"'
            ).join(',')
        )
    ].join('\n');
    
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    
    showToast('CSV をダウンロードしました', 'success');
}

// テーブルソート
function sortTable(tableId, columnIndex, ascending = true) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aCell = a.querySelectorAll('td')[columnIndex];
        const bCell = b.querySelectorAll('td')[columnIndex];
        
        if (!aCell || !bCell) return 0;
        
        const aText = aCell.textContent.trim();
        const bText = bText = bCell.textContent.trim();
        
        const aNum = parseFloat(aText.replace(/[^0-9.-]/g, ''));
        const bNum = parseFloat(bText.replace(/[^0-9.-]/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return ascending ? aNum - bNum : bNum - aNum;
        }
        
        return ascending ? 
            aText.localeCompare(bText, 'ja') : 
            bText.localeCompare(aText, 'ja');
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

// 日付フォーマット
function formatDate(date, format = 'YYYY/MM/DD') {
    if (!date) return 'N/A';
    
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    
    return format
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day)
        .replace('HH', hours)
        .replace('mm', minutes);
}

// 相対時間
function timeAgo(date) {
    if (!date) return '';
    
    const now = new Date();
    const diff = Math.floor((now - new Date(date)) / 1000);
    
    if (diff < 60) return 'たった今';
    if (diff < 3600) return `${Math.floor(diff / 60)}分前`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}時間前`;
    if (diff < 604800) return `${Math.floor(diff / 86400)}日前`;
    
    return formatDate(date);
}

// モバイル判定
function isMobile() {
    return /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
}

// テーマ切り替え
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const themes = ['lofi', 'dark', 'light', 'corporate'];
    const currentIndex = themes.indexOf(currentTheme);
    const nextTheme = themes[(currentIndex + 1) % themes.length];
    
    html.setAttribute('data-theme', nextTheme);
    localStorage.setItem('theme', nextTheme);
    
    showToast(`テーマを ${nextTheme} に変更しました`, 'info');
}

// テーマ初期化
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'lofi';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
});
