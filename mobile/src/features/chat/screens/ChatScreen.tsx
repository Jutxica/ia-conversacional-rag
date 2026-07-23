import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  View,
  ScrollView,
  TouchableOpacity,
  Text,
  TextInput,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView
} from 'react-native';
import {
  LucideMenu,
  LucidePlus,
  LucideSend,
  LucideBookOpen,
  LucideCompass
} from 'lucide-react-native';
import { Colors } from '../../../theme';
import { Conversation, Message, Citation } from '../../../types/chat';
import { StorageService } from '../../../services/StorageService';
import { ChatService } from '../../../services/ChatService';
import { ChatMessage } from '../components/ChatMessage';
import { CitationModal } from '../components/CitationModal';
import { Sidebar } from '../components/Sidebar';
import { useAppContext } from '../../../context/AppContext';

export const ChatScreen: React.FC = () => {
  const { apiUrl, apiKey, setLoginStatus } = useAppContext();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [scope, setScope] = useState('Geral');
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [showSidebar, setShowSidebar] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<(Citation & { idx: number }) | null>(null);

  useEffect(() => {
    const loadConversations = async () => {
      const saved = await StorageService.getConversations();
      setConversations(saved);
      const lastId = await StorageService.getCurrentChatId();
      setCurrentId(lastId);
    };
    loadConversations();
  }, []);

  const saveAndSetConversations = async (newConversations: Conversation[]) => {
    setConversations(newConversations);
    await StorageService.saveConversations(newConversations);
  };

  const toggleSidebar = () => setShowSidebar(!showSidebar);

  const startNewChat = () => {
    const newChatId = 'chat_' + Date.now().toString();
    const newChat: Conversation = {
      id: newChatId,
      title: "Nova Pesquisa",
      messages: [],
      scope: 'Geral'
    };
    const updated = [newChat, ...conversations];
    saveAndSetConversations(updated);
    setCurrentId(newChatId);
    setCurrentConversationId(null);
    if (showSidebar) toggleSidebar();
  };

  const deleteChat = (id: string) => {
    const updated = conversations.filter(c => c.id !== id);
    saveAndSetConversations(updated);
    if (currentId === id) {
      const nextId = updated.length > 0 ? updated[0].id : null;
      setCurrentId(nextId);
      StorageService.saveCurrentChatId(nextId);
    }
  };

  const handleSend = () => {
    if (!input.trim() || isStreaming) return;

    const userMessage: Message = {
      id: 'msg_user_' + Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    let activeChatId = currentId;
    let updatedConversations = [...conversations];

    if (!activeChatId) {
      activeChatId = 'chat_' + Date.now().toString();
      const newChat: Conversation = {
        id: activeChatId,
        title: input.slice(0, 25) + (input.length > 25 ? '...' : ''),
        messages: [userMessage],
        scope: scope
      };
      updatedConversations = [newChat, ...conversations];
      setConversations(updatedConversations);
      setCurrentId(activeChatId);
      StorageService.saveCurrentChatId(activeChatId);
    } else {
      updatedConversations = conversations.map(c => {
        if (c.id === activeChatId) {
          const isFirstMessage = c.messages.length === 0;
          return {
            ...c,
            title: isFirstMessage ? (input.slice(0, 25) + (input.length > 25 ? '...' : '')) : c.title,
            messages: [...c.messages, userMessage]
          };
        }
        return c;
      });
      setConversations(updatedConversations);
    }

    setInput('');
    setIsStreaming(true);

    const activeChat = updatedConversations.find(c => c.id === activeChatId);
    const historyPayload = activeChat
      ? activeChat.messages.slice(0, -1).map(m => ({ role: m.role, content: m.content }))
      : [];

    const assistantMsgId = 'msg_assistant_' + Date.now().toString();

    setConversations(prev => prev.map(c => {
      if (c.id === activeChatId) {
        return {
          ...c,
          messages: [...c.messages, {
            id: assistantMsgId,
            role: 'assistant',
            content: '',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            citations: [],
            metadata: { trust_score: 0 }
          }]
        };
      }
      return c;
    }));

    ChatService.sendStreamRequest({
      apiUrl,
      apiKey,
      query: userMessage.content,
      scope,
      history: historyPayload,
      conversationId: currentConversationId,
      onToken: (token) => {
        setConversations(prev => prev.map(c => {
          if (c.id === activeChatId) {
            return {
              ...c,
              messages: c.messages.map(m =>
                m.id === assistantMsgId ? { ...m, content: m.content + token } : m
              )
            };
          }
          return c;
        }));
      },
      onCitations: (citations) => {
        setConversations(prev => prev.map(c => {
          if (c.id === activeChatId) {
            return {
              ...c,
              messages: c.messages.map(m =>
                m.id === assistantMsgId ? { ...m, citations } : m
              )
            };
          }
          return c;
        }));
      },
      onMetadata: (metadata) => {
        setConversations(prev => prev.map(c => {
          if (c.id === activeChatId) {
            return {
              ...c,
              messages: c.messages.map(m =>
                m.id === assistantMsgId ? { ...m, metadata } : m
              )
            };
          }
          return c;
        }));
      },
      onConversationId: (id) => setCurrentConversationId(id),
      onDone: () => {
        setIsStreaming(false);
        setConversations(prev => {
          StorageService.saveConversations(prev);
          return prev;
        });
      },
      onError: (error) => {
        setIsStreaming(false);
        setConversations(prev => prev.map(c => {
          if (c.id === activeChatId) {
            return {
              ...c,
              messages: c.messages.map(m =>
                m.id === assistantMsgId ? { ...m, content: error } : m
              )
            };
          }
          return c;
        }));
      }
    });
  };

  const selectConversation = (id: string) => {
    setCurrentId(id);
    StorageService.saveCurrentChatId(id);
    const selected = conversations.find(c => c.id === id);
    if (selected && selected.scope) setScope(selected.scope);
    toggleSidebar();
  };

  const activeConversation = conversations.find(c => c.id === currentId);

  return (
    <SafeAreaView style={styles.flex}>
      <View style={styles.header}>
        <TouchableOpacity onPress={toggleSidebar} style={styles.headerBtn}>
          <LucideMenu size={24} color={Colors.textPrimary} />
        </TouchableOpacity>
        <View style={styles.headerTitleContainer}>
          <Text style={styles.headerTitle}>Dehon AI</Text>
          <Text style={styles.headerSub}>Teologia da Reparação</Text>
        </View>
        <TouchableOpacity onPress={startNewChat} style={styles.headerBtn}>
          <LucidePlus size={24} color={Colors.textPrimary} />
        </TouchableOpacity>
      </View>

      <View style={styles.scopeContainer}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.scopeScroll}>
          {['Geral', 'Espiritualidade', 'Social', 'Biografia', 'Correspondencia'].map((item) => (
            <TouchableOpacity
              key={item}
              style={[styles.scopeChip, scope === item && styles.scopeChipActive]}
              onPress={() => setScope(item)}
            >
              <Text style={[styles.scopeText, scope === item && styles.scopeTextActive]}>{item}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      <ScrollView
        style={styles.chatScroll}
        contentContainerStyle={{ paddingBottom: 30 }}
        ref={(ref) => ref?.scrollToEnd({ animated: true })}
      >
        {!activeConversation || activeConversation.messages.length === 0 ? (
          <View style={styles.emptyContainer}>
            <View style={styles.emptyIconContainer}>
              <LucideCompass size={40} color={Colors.primary} />
            </View>
            <Text style={styles.emptyTitle}>Inicie sua Pesquisa Teológica</Text>
            <Text style={styles.emptyDesc}>
              Pergunte algo sobre a vida do Padre Dehon, a teologia do Sagrado Coração, a oblação ou cartas pastorais.
            </Text>

            <View style={styles.suggestions}>
              <TouchableOpacity
                style={styles.suggestionCard}
                onPress={() => setInput("Fale sobre a teologia da reparação no pensamento de Leão Dehon")}
              >
                <Text style={styles.suggestionText}>"Fale sobre a teologia da reparação..."</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.suggestionCard}
                onPress={() => setInput("O que é o conceito de Ecce Venio?")}
              >
                <Text style={styles.suggestionText}>"O que é o conceito de Ecce Venio?"</Text>
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          activeConversation.messages.map((msg) => (
            <View key={msg.id}>
              <ChatMessage message={msg} />
              {msg.role === 'assistant' && msg.citations && msg.citations.length > 0 && (
                <View style={styles.citationsSection}>
                  <View style={styles.citationsHeader}>
                    <LucideBookOpen size={14} color={Colors.primary} />
                    <Text style={styles.citationsHeaderText}>FONTES CONSULTADAS ({msg.citations.length})</Text>
                  </View>
                  <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.citScroll}>
                    {msg.citations.map((cit, cIdx) => (
                      <TouchableOpacity
                        key={cIdx}
                        style={styles.citCard}
                        onPress={() => setSelectedCitation({ ...cit, idx: cIdx + 1 })}
                      >
                        <Text style={styles.citCardTitle} numberOfLines={1}>
                          [{cIdx + 1}] {cit.metadata?.title || 'Documento'}
                        </Text>
                        <Text style={styles.citCardText} numberOfLines={2}>
                          {cit.content}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </ScrollView>
                </View>
              )}
            </View>
          ))
        )}
      </ScrollView>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.chatInput}
            placeholder="Pergunte ao Magistério Dehoniano..."
            placeholderTextColor={Colors.textLight}
            value={input}
            onChangeText={setInput}
            multiline
          />
          <TouchableOpacity
            style={[styles.sendBtn, (!input.trim() || isStreaming) && styles.sendBtnDisabled]}
            onPress={handleSend}
            disabled={!input.trim() || isStreaming}
          >
            {isStreaming ? (
              <ActivityIndicator size="small" color={Colors.white} />
            ) : (
              <LucideSend size={18} color={Colors.white} />
            )}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>

      <Sidebar
        isVisible={showSidebar}
        conversations={conversations}
        currentId={currentId}
        onClose={toggleSidebar}
        onSelectChat={selectConversation}
        onDeleteChat={deleteChat}
        onLogout={() => setLoginStatus(false)}
      />

      <CitationModal
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  header: {
    height: 60,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 15,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
    backgroundColor: Colors.background,
  },
  headerBtn: { padding: 6 },
  headerTitleContainer: { alignItems: 'center' },
  headerTitle: { fontSize: 18, fontWeight: '800', color: Colors.textPrimary },
  headerSub: { fontSize: 10, color: Colors.primary, fontWeight: '700', letterSpacing: 1 },
  scopeContainer: { height: 50, borderBottomWidth: 1, borderBottomColor: Colors.borderLight, backgroundColor: Colors.background },
  scopeScroll: { paddingHorizontal: 15, alignItems: 'center', gap: 10 },
  scopeChip: { paddingHorizontal: 16, paddingVertical: 6, borderRadius: 20, backgroundColor: Colors.borderLight, borderWidth: 1, borderColor: Colors.border },
  scopeChipActive: { backgroundColor: Colors.primary, borderColor: Colors.primary },
  scopeText: { fontSize: 13, color: Colors.textSecondary, fontWeight: '600' },
  scopeTextActive: { color: Colors.background },
  chatScroll: { flex: 1, padding: 15 },
  emptyContainer: { alignItems: 'center', justifyContent: 'center', paddingVertical: 60, paddingHorizontal: 20 },
  emptyIconContainer: { width: 80, height: 80, borderRadius: 40, backgroundColor: Colors.primaryLight, alignItems: 'center', justifyContent: 'center', marginBottom: 20 },
  emptyTitle: { fontSize: 20, fontWeight: '800', color: Colors.textPrimary, marginBottom: 8 },
  emptyDesc: { fontSize: 14, color: Colors.textTertiary, textAlign: 'center', lineHeight: 20, marginBottom: 30 },
  suggestions: { width: '100%', gap: 12 },
  suggestionCard: { backgroundColor: Colors.white, borderWidth: 1, borderColor: Colors.border, borderRadius: 12, padding: 16 },
  suggestionText: { fontSize: 14, color: Colors.textSecondary, fontWeight: '500' },
  inputContainer: { flexDirection: 'row', padding: 15, backgroundColor: Colors.background, borderTopWidth: 1, borderTopColor: Colors.borderLight, alignItems: 'center', gap: 10 },
  chatInput: { flex: 1, backgroundColor: Colors.white, borderWidth: 1, borderColor: Colors.border, borderRadius: 24, paddingHorizontal: 18, paddingVertical: 10, maxHeight: 100, color: Colors.textPrimary, fontSize: 15 },
  sendBtn: { width: 48, height: 48, borderRadius: 24, backgroundColor: Colors.primary, alignItems: 'center', justifyContent: 'center' },
  sendBtnDisabled: { backgroundColor: Colors.border },
  citationsSection: { marginTop: 10, width: '100%', paddingLeft: 10 },
  citationsHeader: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 6 },
  citationsHeaderText: { fontSize: 10, fontWeight: '700', color: Colors.textLight, letterSpacing: 1 },
  citScroll: { paddingBottom: 4 },
  citCard: { width: 200, backgroundColor: Colors.white, borderWidth: 1, borderColor: Colors.border, borderRadius: 12, padding: 12, marginRight: 10 },
  citCardTitle: { fontSize: 12, fontWeight: '700', color: Colors.primary, marginBottom: 4 },
  citCardText: { fontSize: 11, color: Colors.textTertiary, lineHeight: 15 }
});
