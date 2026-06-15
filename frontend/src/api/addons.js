// frontend/src/api/addons.js
// Endpoints des nouvelles fonctionnalités : paiement, livrables, suivi.
// Réutilise le client axios existant (baseURL = .../api, JWT auto).

import apiClient from './axios';

// ==================== PAIEMENT ====================
export const paymentAPI = {
  // card = { card_number, card_name, exp_month, exp_year, cvv, methode? }
  pay: (orderId, card) => apiClient.post(`/orders/${orderId}/pay/`, card),
  status: (orderId) => apiClient.get(`/orders/${orderId}/payment/`),
};

// ==================== SUIVI DE COMMANDE ====================
export const trackingAPI = {
  myOrders: () => apiClient.get('/orders/tracking/'),
  one: (orderId) => apiClient.get(`/orders/${orderId}/tracking/`),
};

// ==================== LIVRABLES (ZIP) ====================
export const deliverablesAPI = {
  list: (orderId) => apiClient.get(`/orders/${orderId}/deliverables/`),

  // Dépôt par le prestataire
  upload: (orderId, file, description = '') => {
    const form = new FormData();
    form.append('fichier', file);
    if (description) form.append('description', description);
    return apiClient.post(`/orders/${orderId}/deliverables/`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  // Téléchargement gardé (renvoie un blob ; échoue en 402 si non payé)
  download: (orderId, livrableId) =>
    apiClient.get(`/orders/${orderId}/deliverables/${livrableId}/download/`, {
      responseType: 'blob',
    }),
};

// Aide : déclenche le téléchargement d'un blob dans le navigateur
export function saveBlob(blob, filename = 'livrable.zip') {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

// ==================== CRUD SERVICE (prestataire) ====================
export const providerServiceAPI = {
  update: (serviceId, data) => apiClient.patch(`/provider/services/${serviceId}/`, data),
  remove: (serviceId) => apiClient.delete(`/provider/services/${serviceId}/`),
};

// ==================== HOMEPAGE — recommandé (public) ====================
export const homeAPI = {
  recommended: () => apiClient.get('/home/recommended/'),
};

// ==================== LITIGES ====================
export const disputesAPI = {
  open: (orderId, description) =>
    apiClient.post(`/orders/${orderId}/dispute/`, { description }),
  mine: () => apiClient.get('/disputes/mine/'),
  // côté admin (app administration)
  adminList: (status = 'open') =>
    apiClient.get('/administration/disputes/', { params: { status } }),
  adminResolve: (disputeId, resolution, admin_note = '') =>
    apiClient.post(`/administration/disputes/${disputeId}/resolve/`, { resolution, admin_note }),
};
