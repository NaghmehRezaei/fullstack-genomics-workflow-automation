import axios from 'axios';
const baseURL = window.location.port === '3000' ? '/api' : 'http://localhost:8000';
export const api = axios.create({baseURL, headers:{'Content-Type':'application/json'}});
export const createAnalysis = async payload => (await api.post('/analyses',payload)).data;
export const getAnalysisStatus = async id => (await api.get(`/analyses/${id}/status`)).data;
export const getAnalysisResults = async id => (await api.get(`/analyses/${id}/results`)).data;
export const getWorkflowDetails = async id => (await api.get(`/analyses/${id}/workflow`)).data;
