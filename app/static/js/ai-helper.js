/**
 * AI 功能助手
 * 处理摘要生成、标题优化、文章生成等功能
 */
class AIHelper {
    constructor() {
        this.apiBase = '/admin/api/ai';
        this.loadingStates = new Map();
    }

    async generate(scene, variables, buttonEl) {
        if (this.loadingStates.get(scene)) {
            alert('AI 正在生成中，请稍候...');
            return null;
        }

        this.setLoading(buttonEl, true);
        this.loadingStates.set(scene, true);

        try {
            const response = await fetch(`${this.apiBase}/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scene, variables })
            });

            const data = await response.json();

            if (data.success) {
                return data.result;
            } else {
                throw new Error(data.message || '生成失败');
            }
        } catch (error) {
            console.error('AI 生成失败:', error);
            alert(`❌ AI 生成失败: ${error.message}`);
            return null;
        } finally {
            this.setLoading(buttonEl, false);
            this.loadingStates.delete(scene);
        }
    }

    setLoading(buttonEl, isLoading) {
        if (!buttonEl) return;
        const originalText = buttonEl.getAttribute('data-original-text');
        if (isLoading) {
            buttonEl.setAttribute('data-original-text', buttonEl.textContent);
            buttonEl.textContent = '生成中...';
            buttonEl.disabled = true;
        } else {
            buttonEl.textContent = originalText || buttonEl.textContent;
            buttonEl.disabled = false;
        }
    }
}

// 初始化所有 AI 按钮
function initAIButtons() {
    const aiHelper = new AIHelper();

    // 标题优化按钮
    const titleBtn = document.getElementById('ai-title-btn');
    if (titleBtn) {
        titleBtn.addEventListener('click', async function() {
            const content = document.getElementById('markdown_content')?.value || '';
            if (!content.trim()) {
                alert('请先输入文章内容，再进行标题优化');
                return;
            }

            const result = await aiHelper.generate('title', { content }, this);
            if (result) {
                showTitleOptions(result);
            }
        });
    }

    // 摘要生成按钮
    const summaryBtn = document.getElementById('ai-summary-btn');
    if (summaryBtn) {
        summaryBtn.addEventListener('click', async function() {
            const content = document.getElementById('markdown_content')?.value || '';
            if (!content.trim()) {
                alert('请先输入文章内容，再生成摘要');
                return;
            }

            const result = await aiHelper.generate('summary', { content }, this);
            if (result) {
                document.getElementById('summary').value = result.trim();
                alert('✅ 摘要已生成！');
            }
        });
    }

    // 文章生成按钮
    const generateBtn = document.getElementById('ai-generate-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', async function() {
            const topic = prompt('📝 请输入文章主题：');
            if (!topic) return;

            const requirements = prompt('🎯 请输入额外要求（可选）：\n例如：结构清晰、内容详实、约1000字、包含代码示例等', '');

            const result = await aiHelper.generate('generate', {
                topic: topic,
                requirements: requirements || '结构清晰，内容详实'
            }, this);

            if (result) {
                const editor = document.getElementById('markdown_content');
                const oldContent = editor.value;
                editor.value = result.trim() + '\n\n' + oldContent;

                // 触发编辑器更新事件
                const event = new Event('input', { bubbles: true });
                editor.dispatchEvent(event);

                alert('✅ 文章已生成！');
            }
        });
    }
}

function showTitleOptions(titlesText) {
    const titles = titlesText.trim().split('\n').filter(t => t.trim());

    if (titles.length === 0) {
        alert('未生成有效标题，请重试');
        return;
    }

    let message = `🤖 AI 为您生成了 ${titles.length} 个标题建议：\n\n`;
    titles.forEach((title, index) => {
        message += `${index + 1}. ${title.replace(/^\d+[\.\)\s]\s*/, '')}\n`;
    });
    message += '\n请输入您选择的标题序号（或直接输入自定义标题）：';

    const selected = prompt(message, titles[0].replace(/^\d+[\.\)\s]\s*/, ''));

    if (selected) {
        // 如果是数字序号，提取对应的标题
        const indexMatch = selected.match(/^(\d+)$/);
        if (indexMatch && indexMatch[1] <= titles.length) {
            const index = parseInt(indexMatch[1]) - 1;
            document.getElementById('title').value = titles[index].replace(/^\d+[\.\)\s]\s*/, '').trim();
        } else {
            document.getElementById('title').value = selected;
        }
    }
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAIButtons);
} else {
    initAIButtons();
}
