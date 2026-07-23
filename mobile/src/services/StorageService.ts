import AsyncStorage from '@react-native-async-storage/async-storage';
import { Conversation } from '../types/chat';

const KEYS = {
  API_URL: '@api_url',
  API_KEY: '@api_key',
  CONVERSATIONS: '@conversations',
  CURRENT_ID: '@current_id',
  IS_LOGGED: '@is_logged',
};

export const StorageService = {
  async saveApiConfig(url: string, key: string) {
    await AsyncStorage.setItem(KEYS.API_URL, url);
    await AsyncStorage.setItem(KEYS.API_KEY, key);
  },

  async getApiConfig() {
    const url = await AsyncStorage.getItem(KEYS.API_URL);
    const key = await AsyncStorage.getItem(KEYS.API_KEY);
    return { url, key };
  },

  async saveConversations(conversations: Conversation[]) {
    await AsyncStorage.setItem(KEYS.CONVERSATIONS, JSON.stringify(conversations));
  },

  async getConversations(): Promise<Conversation[]> {
    const data = await AsyncStorage.getItem(KEYS.CONVERSATIONS);
    return data ? JSON.parse(data) : [];
  },

  async saveCurrentChatId(id: string | null) {
    if (id) {
      await AsyncStorage.setItem(KEYS.CURRENT_ID, id);
    } else {
      await AsyncStorage.removeItem(KEYS.CURRENT_ID);
    }
  },

  async getCurrentChatId() {
    return await AsyncStorage.getItem(KEYS.CURRENT_ID);
  },

  async setLoginStatus(status: boolean) {
    await AsyncStorage.setItem(KEYS.IS_LOGGED, String(status));
  },

  async getLoginStatus() {
    const status = await AsyncStorage.getItem(KEYS.IS_LOGGED);
    return status === 'true';
  },

  async clearAll() {
    await AsyncStorage.clear();
  }
};
