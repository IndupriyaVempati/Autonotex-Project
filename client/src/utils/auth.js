const TOKEN_KEY = 'autonotex_token';
const USER_KEY = 'autonotex_user';

export const getToken = () => localStorage.getItem(TOKEN_KEY);

export const setAuth = (token, user) => {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  }
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
};

export const clearAuth = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

export const getStoredUser = () => {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (err) {
    return null;
  }
};

export const getAuthHeader = () => {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};
