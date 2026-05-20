/**
 * Markdown 编辑器 - 支持实时预览、快捷按钮、粘贴图片上传
 */
class MarkdownEditor {
    constructor(options = {}) {
        this.editorId = options.editorId || 'markdown_content';
        this.previewId = options.previewId || 'markdown_preview';
        this.uploadUrl = options.uploadUrl || '/admin/api/upload-image';

        this.editor = document.getElementById(this.editorId);
        this.preview = document.getElementById(this.previewId);

        if (!this.editor) {
            console.error('Markdown editor not found:', this.editorId);
            return;
        }

        this.isSyncScrolling = false;
        this.init();
    }

    init() {
        // 实时预览
        if (this.preview) {
            this.editor.addEventListener('input', () => this.updatePreview());
            this.updatePreview();
            // 同步滚动
            this.initSyncScroll();
        }

        // 粘贴图片自动上传
        this.editor.addEventListener('paste', (e) => this.handlePaste(e));

        // 快捷按钮事件
        this.initToolbar();

        // 可拖拽分隔条
        this.initSplitter();
    }

    initSplitter() {
        const splitter = document.querySelector('.md-splitter');
        const container = document.querySelector('.md-editor-container');

        if (!splitter || !container) return;

        let isDragging = false;

        const handleMouseDown = (e) => {
            isDragging = true;
            splitter.classList.add('active');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        };

        const handleMouseMove = (e) => {
            if (!isDragging) return;

            const containerRect = container.getBoundingClientRect();
            const totalWidth = containerRect.width;
            const mouseX = e.clientX - containerRect.left;

            // 计算比例，限制最小宽度为20%
            const leftPercentage = Math.max(20, Math.min(80, (mouseX / totalWidth) * 100));
            const rightPercentage = 100 - leftPercentage;

            container.style.gridTemplateColumns = `${leftPercentage}% 6px ${rightPercentage}%`;
        };

        const handleMouseUp = () => {
            isDragging = false;
            splitter.classList.remove('active');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };

        splitter.addEventListener('mousedown', handleMouseDown);
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    }

    initSyncScroll() {
        // 编辑器滚动时同步到预览
        this.editor.addEventListener('scroll', () => {
            if (this.isSyncScrolling) return;
            this.isSyncScrolling = true;

            const scrollRatio = this.editor.scrollTop / (this.editor.scrollHeight - this.editor.clientHeight);
            const previewScrollTop = scrollRatio * (this.preview.scrollHeight - this.preview.clientHeight);
            this.preview.scrollTop = previewScrollTop;

            requestAnimationFrame(() => {
                this.isSyncScrolling = false;
            });
        });

        // 预览滚动时同步到编辑器
        this.preview.addEventListener('scroll', () => {
            if (this.isSyncScrolling) return;
            this.isSyncScrolling = true;

            const scrollRatio = this.preview.scrollTop / (this.preview.scrollHeight - this.preview.clientHeight);
            const editorScrollTop = scrollRatio * (this.editor.scrollHeight - this.editor.clientHeight);
            this.editor.scrollTop = editorScrollTop;

            requestAnimationFrame(() => {
                this.isSyncScrolling = false;
            });
        });
    }

    initToolbar() {
        const toolbar = document.querySelector('.md-toolbar');
        if (!toolbar) return;

        toolbar.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const markdown = btn.dataset.markdown;
                if (markdown) {
                    e.preventDefault();
                    if (markdown.includes('{{selected}}')) {
                        const [prefix, suffix] = markdown.split('{{selected}}');
                        this.insertMarkdown(prefix, suffix);
                    } else {
                        this.insertMarkdown(markdown);
                    }
                }
            });
        });
    }

    async updatePreview() {
        if (!this.preview || typeof marked === 'undefined') return;

        const text = this.editor.value;

        try {
            const html = marked.parse(text);
            this.preview.innerHTML = html;
        } catch (error) {
            this.preview.innerHTML = '<p style="color: #ef4444;">Markdown 解析错误: ' + error.message + '</p>';
        }
    }

    insertMarkdown(prefix, suffix = '') {
        const start = this.editor.selectionStart;
        const end = this.editor.selectionEnd;
        const selectedText = this.editor.value.substring(start, end);

        this.editor.focus();

        // 使用 document.execCommand 支持撤销
        if (selectedText) {
            // 先删除选中的文本
            document.execCommand('delete', false, null);
        }
        // 插入前缀
        document.execCommand('insertText', false, prefix);
        // 插入选中的文本
        if (selectedText) {
            document.execCommand('insertText', false, selectedText);
        }
        // 插入后缀
        document.execCommand('insertText', false, suffix);

        // 重置光标位置到中间
        const newCursorPos = start + prefix.length + (selectedText?.length || 0);
        this.editor.selectionStart = this.editor.selectionEnd = newCursorPos;

        this.updatePreview();
        this.editor.focus();
    }

    async handlePaste(e) {
        const items = e.clipboardData?.items;
        if (!items) return;

        // 查找图片文件
        for (let item of items) {
            if (item.type.startsWith('image/')) {
                e.preventDefault();
                const file = item.getAsFile();
                if (file) {
                    await this.uploadImage(file);
                }
                break;
            }
        }
    }

    async uploadImage(file) {
        this.showStatus('正在上传图片...', 'info');

        const formData = new FormData();
        formData.append('image', file);

        try {
            const response = await fetch(this.uploadUrl, {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            });

            const result = await response.json();

            if (result.success && result.url) {
                const imageMarkdown = `![图片](${result.url})`;
                this.insertMarkdown(imageMarkdown);
                this.showStatus('图片上传成功！', 'success');
            } else {
                this.showStatus(result.message || '上传失败', 'error');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showStatus('上传失败: ' + error.message, 'error');
        }
    }

    showStatus(message, type = 'info') {
        let statusEl = document.getElementById('md-editor-status');
        if (!statusEl) {
            statusEl = document.createElement('div');
            statusEl.id = 'md-editor-status';
            statusEl.className = `md-status-${type}`;
            this.editor.parentNode.insertBefore(statusEl, this.editor.nextSibling);
        }

        statusEl.className = `md-status-${type}`;
        statusEl.textContent = message;
        statusEl.style.display = 'block';

        // 3秒后隐藏成功消息
        if (type === 'success') {
            setTimeout(() => {
                statusEl.style.display = 'none';
            }, 3000);
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 检查是否有 Markdown 编辑器
    if (document.getElementById('markdown_content')) {
        new MarkdownEditor();
    }
});
