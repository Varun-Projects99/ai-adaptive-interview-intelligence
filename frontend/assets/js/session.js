async function apiPost(url, data, isFormData = false) {
  const options = {
    method: 'POST',
    headers: {
      'Content-Type': isFormData ? undefined : 'application/json',
    },
    body: isFormData ? data : JSON.stringify(data),
  };

  if (isFormData) {
    // For FormData, let the browser set the 'Content-Type' header
    delete options.headers['Content-Type'];
  }

  const response = await fetch(url, options);
  const contentType = response.headers.get("content-type") || "";
  let result = null;

  if (contentType.includes("application/json")) {
    try {
      result = await response.json();
    } catch (e) {
      throw new Error(`Failed to parse JSON response from ${url}: ${e.message}`);
    }
  }

  if (!response.ok) {
    const errMsg = (result && result.error) ? result.error : `HTTP ${response.status} Error from ${url}`;
    throw new Error(errMsg);
  }

  if (!contentType.includes("application/json")) {
    throw new Error(`Server returned non-JSON response from ${url}`);
  }

  return result;
}

// Global toast notification function
function showToast(message, type = 'info') {
  const toast = document.getElementById('toast');
  if (!toast) return;

  toast.textContent = message;
  toast.className = 'toast show ' + type;

  setTimeout(() => {
    toast.classList.remove('show');
  }, 3000);
}

const Session = {
  get id() {
    return localStorage.getItem('session_id');
  },
  set id(val) {
    localStorage.setItem('session_id', val || '');
  },

  get skills() {
    try {
      return JSON.parse(localStorage.getItem('session_skills') || '[]');
    } catch(e) {
      return [];
    }
  },
  set skills(val) {
    localStorage.setItem('session_skills', JSON.stringify(val || []));
  },

  get total() {
    return parseInt(localStorage.getItem('session_total') || '0', 10);
  },
  set total(val) {
    localStorage.setItem('session_total', String(val || 0));
  },

  clear: function() {
    localStorage.removeItem('session_id');
    localStorage.removeItem('session_skills');
    localStorage.removeItem('session_total');
  }
};

// Global logout function
async function logout() {
  try {
    await apiPost('/api/auth/logout', {});
    Session.clear();
    window.location.href = '/';
  } catch (e) {
    console.error('Logout failed:', e);
    window.location.href = '/';
  }
}