// Placeholder for API POST requests (if needed)
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
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.error || 'Something went wrong');
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
  id: null,
  skills: [],
  total: 0,

  setLoggedIn: function(isLoggedIn) {
    localStorage.setItem('isLoggedIn', isLoggedIn ? 'true' : 'false');
  },

  isLoggedIn: function() {
    return localStorage.getItem('isLoggedIn') === 'true';
  },

  // Other session related methods can be added here
};

// Check login status on pages that require it
// (e.g., dashboard, interview page)
// This is a simplified check for frontend-only redirects
// A more robust solution would involve backend session validation
if (window.location.pathname === '/dashboard' || window.location.pathname === '/interview') {
  if (!Session.isLoggedIn()) {
    window.location.href = '/'; // Redirect to login page
  }
}