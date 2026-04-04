import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE = process.env.EXPO_PUBLIC_BACKEND_URL || '';

async function getToken(): Promise<string | null> {
  return AsyncStorage.getItem('access_token');
}

async function getRefreshToken(): Promise<string | null> {
  return AsyncStorage.getItem('refresh_token');
}

async function request(path: string, options: RequestInit = {}): Promise<any> {
  const token = await getToken();
  const headers: any = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    // Try refresh
    const refreshToken = await getRefreshToken();
    if (refreshToken) {
      const refreshRes = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (refreshRes.ok) {
        const data = await refreshRes.json();
        await AsyncStorage.setItem('access_token', data.access_token);
        headers['Authorization'] = `Bearer ${data.access_token}`;
        const retryRes = await fetch(`${API_BASE}${path}`, { ...options, headers });
        if (!retryRes.ok) {
          const err = await retryRes.json().catch(() => ({}));
          throw new Error(err.detail || `Request failed: ${retryRes.status}`);
        }
        return retryRes.json();
      }
    }
    await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user']);
    throw new Error('Session expired');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = err.detail;
    if (typeof detail === 'string') throw new Error(detail);
    if (Array.isArray(detail)) throw new Error(detail.map((e: any) => e.msg || JSON.stringify(e)).join(' '));
    throw new Error(`Request failed: ${res.status}`);
  }

  return res.json();
}

// Auth
export const api = {
  register: (name: string, email: string, password: string) =>
    request('/api/v1/auth/register', { method: 'POST', body: JSON.stringify({ name, email, password }) }),

  login: (email: string, password: string) =>
    request('/api/v1/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),

  getMe: () => request('/api/v1/auth/me'),

  updateProfile: (data: any) =>
    request('/api/v1/auth/profile', { method: 'PUT', body: JSON.stringify(data) }),

  // Fridge
  getFridge: () => request('/api/v1/fridge'),

  addIngredients: (ingredients: any[]) =>
    request('/api/v1/fridge/manual', { method: 'POST', body: JSON.stringify({ ingredients }) }),

  updateFridgeItem: (itemId: string, data: any) =>
    request(`/api/v1/fridge/${itemId}`, { method: 'PUT', body: JSON.stringify(data) }),

  deleteFridgeItem: (itemId: string) =>
    request(`/api/v1/fridge/${itemId}`, { method: 'DELETE' }),

  // Recipes
  generateRecipe: (data: any) =>
    request('/api/v1/recipes/generate', { method: 'POST', body: JSON.stringify(data) }),

  getMyRecipes: () => request('/api/v1/recipes/my'),

  getRecipe: (recipeId: string) => request(`/api/v1/recipes/${recipeId}`),

  getCookingData: (recipeId: string) => request(`/api/v1/recipes/${recipeId}/cook`),

  toggleFavorite: (recipeId: string) =>
    request(`/api/v1/recipes/${recipeId}/favorite`, { method: 'POST' }),

  getFavorites: () => request('/api/v1/recipes/favorites'),

  doneCooking: (recipeId: string) =>
    request(`/api/v1/recipes/${recipeId}/done-cooking`, { method: 'POST' }),
};
