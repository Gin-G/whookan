// assets/js/forum.js

const params = new URLSearchParams(window.location.search);
const SKILL_ID = params.get('skill_id');
const SKILL_NAME = params.get('skill_name') || 'Skill Forum';

let currentPostId = null;

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;

    if (!SKILL_ID) {
        showError('No skill specified.');
        return;
    }

    // Set page title and links
    document.getElementById('forum-skill-name').textContent = SKILL_NAME + ' Forum';
    document.title = 'WhoKan – ' + SKILL_NAME + ' Forum';
    const chatUrl = `/chat.html?skill_id=${encodeURIComponent(SKILL_ID)}&skill_name=${encodeURIComponent(SKILL_NAME)}`;
    document.getElementById('chat-link').href = chatUrl;

    loadPosts();

    // New post button
    document.getElementById('new-post-btn').addEventListener('click', () => {
        document.getElementById('new-post-modal').classList.remove('hidden');
    });
    document.getElementById('cancel-post-btn').addEventListener('click', () => {
        document.getElementById('new-post-modal').classList.add('hidden');
    });

    // New post form submit
    document.getElementById('new-post-form').addEventListener('submit', handleCreatePost);

    // Back button in detail view
    document.getElementById('back-btn').addEventListener('click', showPostList);

    // Vote button in detail view
    document.getElementById('vote-btn').addEventListener('click', handleVote);

    // Comment form submit
    document.getElementById('comment-form').addEventListener('submit', handleAddComment);
});

// ---------------------------------------------------------------------------
// Load and render post list
// ---------------------------------------------------------------------------

async function loadPosts() {
    document.getElementById('posts-loading').classList.remove('hidden');
    document.getElementById('posts-list').classList.add('hidden');
    document.getElementById('posts-empty').classList.add('hidden');

    try {
        const posts = await api.getForumPosts(SKILL_ID);
        renderPostList(posts);
    } catch (err) {
        showError(err.message || 'Failed to load posts.');
    } finally {
        document.getElementById('posts-loading').classList.add('hidden');
    }
}

function renderPostList(posts) {
    const list = document.getElementById('posts-list');
    list.innerHTML = '';

    if (!posts || posts.length === 0) {
        document.getElementById('posts-empty').classList.remove('hidden');
        return;
    }

    posts.forEach(post => {
        const li = document.createElement('li');
        li.className = 'px-4 py-4 hover:bg-gray-50 cursor-pointer';
        li.innerHTML = `
            <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                    <h3 class="text-sm font-medium text-gray-900 truncate">${escapeHtml(post.title)}</h3>
                    <p class="text-xs text-gray-500 mt-0.5">
                        by ${escapeHtml(post.author_name)} · ${formatDate(post.created_at)}
                    </p>
                    <p class="text-sm text-gray-600 mt-1 line-clamp-2">${escapeHtml(post.body)}</p>
                </div>
                <div class="ml-4 flex-shrink-0 flex flex-col items-center text-xs text-gray-400 gap-1">
                    <span>▲ ${post.vote_count}</span>
                    <span>💬 ${post.comment_count}</span>
                </div>
            </div>
        `;
        li.addEventListener('click', () => openPostDetail(post.id));
        list.appendChild(li);
    });

    list.classList.remove('hidden');
}

// ---------------------------------------------------------------------------
// Post detail
// ---------------------------------------------------------------------------

async function openPostDetail(postId) {
    currentPostId = postId;
    document.getElementById('post-detail').classList.remove('hidden');
    document.getElementById('posts-list').classList.add('hidden');
    document.getElementById('posts-empty').classList.add('hidden');
    document.getElementById('new-post-btn').classList.add('hidden');
    document.getElementById('chat-link').classList.add('hidden');

    try {
        const post = await api.getForumPost(SKILL_ID, postId);
        renderPostDetail(post);
    } catch (err) {
        showError(err.message || 'Failed to load post.');
    }
}

function renderPostDetail(post) {
    document.getElementById('detail-title').textContent = post.title;
    document.getElementById('detail-meta').textContent =
        `by ${post.author_name} · ${formatDate(post.created_at)}`;
    document.getElementById('detail-body').textContent = post.body;

    const voteBtn = document.getElementById('vote-btn');
    document.getElementById('vote-count').textContent = post.vote_count;
    voteBtn.className = post.user_voted
        ? 'inline-flex items-center px-3 py-1.5 border border-indigo-500 text-sm font-medium rounded-md text-indigo-700 bg-indigo-50'
        : 'inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50';

    renderComments(post.comments, post.comment_count);
}

function renderComments(comments, count) {
    document.getElementById('comment-count').textContent = `(${count})`;
    const list = document.getElementById('comments-list');
    list.innerHTML = '';

    comments.forEach(comment => {
        const li = document.createElement('li');
        li.className = 'bg-gray-50 rounded-md px-3 py-2';
        li.innerHTML = `
            <div class="flex items-center gap-2 text-xs text-gray-500 mb-1">
                <span class="font-medium text-gray-700">${escapeHtml(comment.author_name)}</span>
                <span>${formatDate(comment.created_at)}</span>
            </div>
            <p class="text-sm text-gray-800">${escapeHtml(comment.body)}</p>
        `;
        list.appendChild(li);
    });
}

function showPostList() {
    currentPostId = null;
    document.getElementById('post-detail').classList.add('hidden');
    document.getElementById('new-post-btn').classList.remove('hidden');
    document.getElementById('chat-link').classList.remove('hidden');
    loadPosts();
}

// ---------------------------------------------------------------------------
// Create post
// ---------------------------------------------------------------------------

async function handleCreatePost(event) {
    event.preventDefault();
    const title = document.getElementById('post-title').value.trim();
    const body = document.getElementById('post-body').value.trim();
    const btn = document.getElementById('submit-post-btn');
    btn.disabled = true;

    try {
        await api.createForumPost(SKILL_ID, { title, body });
        document.getElementById('new-post-modal').classList.add('hidden');
        document.getElementById('post-title').value = '';
        document.getElementById('post-body').value = '';
        loadPosts();
    } catch (err) {
        showError(err.message || 'Failed to create post.');
    } finally {
        btn.disabled = false;
    }
}

// ---------------------------------------------------------------------------
// Vote
// ---------------------------------------------------------------------------

async function handleVote() {
    if (!currentPostId) return;
    try {
        const result = await api.voteForumPost(SKILL_ID, currentPostId);
        document.getElementById('vote-count').textContent = result.vote_count;
        const voteBtn = document.getElementById('vote-btn');
        voteBtn.className = result.voted
            ? 'inline-flex items-center px-3 py-1.5 border border-indigo-500 text-sm font-medium rounded-md text-indigo-700 bg-indigo-50'
            : 'inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50';
    } catch (err) {
        showError(err.message || 'Failed to vote.');
    }
}

// ---------------------------------------------------------------------------
// Add comment
// ---------------------------------------------------------------------------

async function handleAddComment(event) {
    event.preventDefault();
    const input = document.getElementById('comment-input');
    const body = input.value.trim();
    if (!body || !currentPostId) return;

    try {
        await api.addForumComment(SKILL_ID, currentPostId, { body });
        input.value = '';
        // Reload post detail to show updated comments + count
        const post = await api.getForumPost(SKILL_ID, currentPostId);
        renderPostDetail(post);
    } catch (err) {
        showError(err.message || 'Failed to post comment.');
    }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
