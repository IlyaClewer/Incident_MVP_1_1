async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers ?? {}),
    },
    ...options,
  })

  if (!response.ok) {
    let detail = `HTTP ${response.status}`

    try {
      const payload = await response.json()
      detail =
        payload?.detail?.message ??
        payload?.detail ??
        payload?.message ??
        detail
    } catch {
      // Keep the fallback message when the server does not return JSON.
    }

    throw new Error(
      typeof detail === 'string' ? detail : JSON.stringify(detail)
    )
  }

  if (response.status === 204) {
    return null
  }

  return response.json()
}

export const api = {
  getPatients() {
    return request('/patients')
  },

  getMeta() {
    return request('/meta')
  },

  getStacCardEvents(stacCardId) {
    return request(`/stac-cards/${stacCardId}/events`)
  },

  updateDiagnosisState(diagnosisStateId, payload) {
    return request(`/diagnosis-states/${diagnosisStateId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },

  transferDiagnosisEvents(diagnosisStateId, payload) {
    return request(`/diagnosis-states/${diagnosisStateId}/transfer`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  getExpertGroups() {
    return request('/catalogs/expert-groups')
  },

  createExpertGroup(payload) {
    return request('/catalogs/expert-groups', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  updateExpertGroup(groupId, payload) {
    return request(`/catalogs/expert-groups/${groupId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },

  deleteExpertGroup(groupId) {
    return request(`/catalogs/expert-groups/${groupId}`, {
      method: 'DELETE',
    })
  },

  getDiagnosisTypes() {
    return request('/catalogs/diagnosis-types')
  },

  createDiagnosisType(payload) {
    return request('/catalogs/diagnosis-types', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  updateDiagnosisType(diagnosisId, payload) {
    return request(`/catalogs/diagnosis-types/${diagnosisId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },

  deleteDiagnosisType(diagnosisId) {
    return request(`/catalogs/diagnosis-types/${diagnosisId}`, {
      method: 'DELETE',
    })
  },

  getEventTypes() {
    return request('/catalogs/event-types')
  },

  createEventType(payload) {
    return request('/catalogs/event-types', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  updateEventType(eventTypeId, payload) {
    return request(`/catalogs/event-types/${eventTypeId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },

  deleteEventType(eventTypeId) {
    return request(`/catalogs/event-types/${eventTypeId}`, {
      method: 'DELETE',
    })
  },
}
