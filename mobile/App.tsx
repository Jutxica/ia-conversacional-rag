import React, { useState, useEffect, useRef } from 'react';
import { 
  StyleSheet, 
  View, 
  Dimensions, 
  KeyboardAvoidingView, 
  Platform, 
  Text, 
  ScrollView, 
  TouchableOpacity,
  TextInput,
  Animated,
  Modal,
  ActivityIndicator,
  SafeAreaView
} from 'react-native';
import { 
  LucideChevronRight, 
  LucideMenu, 
  LucidePlus, 
  LucideLogOut, 
  LucideSettings, 
  LucideSend, 
  LucideBookOpen, 
  LucideX, 
  LucideAlertTriangle,
  LucideCompass
} from 'lucide-react-native';
import { StatusBar as ExpoStatusBar } from 'expo-status-bar';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width, height } = Dimensions.get('window');

// Interfaces
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: any[];
  metadata?: {
    trust_score?: number;
    [key: string]: any;
  };
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  conversation_id?: string;
  scope?: string;
}

// Configurações padrão
const DEFAULT_API_URL = "https://dehon-ai-dehon-ai.xgaqg9.easypanel.host";
const DEFAULT_API_KEY = "e94c9ba1ba74aee889b5c5fe3e0a6521";

// --- Componente: Splash Screen ---
const SplashScreen = ({ onFinish }: { onFinish: () => void }) => {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.85)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        friction: 5,
        useNativeDriver: true,
      })
    ]).start();

    const timer = setTimeout(onFinish, 2500);
    return () => clearTimeout(timer);
  }, []);

  return (
    <View style={styles.splashContainer}>
      <Animated.View style={[styles.splashContent, { opacity: fadeAnim, transform: [{ scale: scaleAnim }] }]}>
        <View style={styles.logoCircle}>
          <Text style={styles.logoText}>D</Text>
        </View>
        <Text style={styles.splashTitle}>DEHON AI</Text>
        <Text style={styles.splashSubtitle}>BIBLIOTECA ACADÊMICA</Text>
      </Animated.View>
    </View>
  );
};

// --- Componente principal do App ---
export default function App() {
  const [showSplash, setShowSplash] = useState(true);
  const [isLogged, setIsLogged] = useState(false);
  const [apiUrl, setApiUrl] = useState(DEFAULT_API_URL);
  const [apiKey, setApiKey] = useState(DEFAULT_API_KEY);
  const [showConfig, setShowConfig] = useState(false);

  // States do Chat
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [scope, setScope] = useState('Geral');
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [showSidebar, setShowSidebar] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<any | null>(null);

  // Lógica de animação do Sidebar
  const sidebarAnim = useRef(new Animated.Value(-width * 0.75)).current;

  // Carregar dados salvos no início
  useEffect(() => {
    const loadAppData = async () => {
      try {
        const savedUrl = await AsyncStorage.getItem('@api_url');
        const savedKey = await AsyncStorage.getItem('@api_key');
        const savedConversations = await AsyncStorage.getItem('@conversations');
        const savedCurrentId = await AsyncStorage.getItem('@current_id');
        const loginStatus = await AsyncStorage.getItem('@is_logged');

        if (savedUrl) setApiUrl(savedUrl);
        if (savedKey) setApiKey(savedKey);
        if (loginStatus === 'true') setIsLogged(true);
        if (savedConversations) {
          setConversations(JSON.parse(savedConversations));
        }
        if (savedCurrentId) setCurrentId(savedCurrentId);
      } catch (e) {
        console.error("Erro ao carregar dados locais", e);
      }
    };
    loadAppData();
  }, []);

  // Salvar conversas sempre que mudarem
  const saveConversations = async (newConversations: Conversation[]) => {
    try {
      await AsyncStorage.setItem('@conversations', JSON.stringify(newConversations));
    } catch (e) {
      console.error("Erro ao salvar conversas", e);
    }
  };

  // Alternar Sidebar com animação
  const toggleSidebar = () => {
    const toValue = showSidebar ? -width * 0.75 : 0;
    Animated.timing(sidebarAnim, {
      toValue,
      duration: 250,
      useNativeDriver: false
    }).start();
    setShowSidebar(!showSidebar);
  };

  // Iniciar nova conversa
  const startNewChat = () => {
    const newChatId = 'chat_' + Date.now().toString();
    const newChat: Conversation = {
      id: newChatId,
      title: "Nova Pesquisa",
      messages: [],
      scope: 'Geral'
    };
    const updated = [newChat, ...conversations];
    setConversations(updated);
    setCurrentId(newChatId);
    setCurrentConversationId(null);
    saveConversations(updated);
    if (showSidebar) toggleSidebar();
  };

  // Excluir conversa
  const deleteChat = (id: string) => {
    const updated = conversations.filter(c => c.id !== id);
    setConversations(updated);
    saveConversations(updated);
    if (currentId === id) {
      setCurrentId(updated.length > 0 ? updated[0].id : null);
    }
  };

  // Lógica de Login
  const handleLogin = async () => {
    try {
      await AsyncStorage.setItem('@api_url', apiUrl);
      await AsyncStorage.setItem('@api_key', apiKey);
      await AsyncStorage.setItem('@is_logged', 'true');
      setIsLogged(true);
    } catch (e) {
      console.error(e);
    }
  };

  // Lógica de Logout
  const handleLogout = async () => {
    try {
      await AsyncStorage.removeItem('@is_logged');
      setIsLogged(false);
    } catch (e) {
      console.error(e);
    }
  };

  // Lógica do Chat Stream (SSE)
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

    // Se não tiver conversa ativa, cria uma na hora
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

    saveConversations(updatedConversations);
    setInput('');
    setIsStreaming(true);

    const activeChat = updatedConversations.find(c => c.id === activeChatId);
    const historyPayload = activeChat 
      ? activeChat.messages.slice(0, -1).map(m => ({ role: m.role, content: m.content })) 
      : [];

    const assistantMsgId = 'msg_assistant_' + Date.now().toString();

    // Adiciona o balão vazio do assistente para ir recebendo os tokens
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

    // Inicia a requisição XML HTTP para o stream
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${apiUrl}/api/chat`, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    if (apiKey) {
      xhr.setRequestHeader('Authorization', `Bearer ${apiKey}`);
    }

    const payload = {
      query: input,
      scope: scope,
      history: historyPayload,
      conversation_id: currentConversationId,
      categories: []
    };

    let position = 0;

    xhr.onreadystatechange = () => {
      if (xhr.readyState === 3 || xhr.readyState === 4) {
        const responseText = xhr.responseText;
        const newChunk = responseText.substring(position);
        position = responseText.length;

        const lines = newChunk.split('\n');
        for (let line of lines) {
          line = line.trim();
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'token') {
                setConversations(prev => prev.map(c => {
                  if (c.id === activeChatId) {
                    return {
                      ...c,
                      messages: c.messages.map(m => 
                        m.id === assistantMsgId ? { ...m, content: m.content + data.content } : m
                      )
                    };
                  }
                  return c;
                }));
              } else if (data.type === 'citations') {
                setConversations(prev => prev.map(c => {
                  if (c.id === activeChatId) {
                    return {
                      ...c,
                      messages: c.messages.map(m => 
                        m.id === assistantMsgId ? { ...m, citations: data.content } : m
                      )
                    };
                  }
                  return c;
                }));
              } else if (data.type === 'metadata') {
                setConversations(prev => prev.map(c => {
                  if (c.id === activeChatId) {
                    return {
                      ...c,
                      messages: c.messages.map(m => 
                        m.id === assistantMsgId ? { ...m, metadata: data.content } : m
                      )
                    };
                  }
                  return c;
                }));
              } else if (data.type === 'conversation_id') {
                setCurrentConversationId(data.conversation_id || data.content);
              } else if (data.type === 'done') {
                setIsStreaming(false);
              }
            } catch (e) {
              // Fragmento de linha incompleto, ignora
            }
          }
        }
      }

      if (xhr.readyState === 4) {
        setIsStreaming(false);
        setConversations(prev => {
          saveConversations(prev);
          return prev;
        });
      }
    };

    xhr.onerror = () => {
      setIsStreaming(false);
      setConversations(prev => prev.map(c => {
        if (c.id === activeChatId) {
          return {
            ...c,
            messages: c.messages.map(m => 
              m.id === assistantMsgId 
                ? { ...m, content: "Erro ao conectar ao servidor. Por favor, verifique sua conexão ou URL da API." } 
                : m
            )
          };
        }
        return c;
      }));
    };

    xhr.send(JSON.stringify(payload));
  };

  // Renderizar o conteúdo formatado em Markdown simples (bold e listas)
  const renderMessageContent = (text: string) => {
    if (!text) return <ActivityIndicator size="small" color="#9f1239" />;
    
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      const isBullet = line.trim().startsWith('-') || line.trim().startsWith('*');
      const cleanLine = isBullet ? line.trim().replace(/^[-*]\s*/, '') : line;
      
      const parts = cleanLine.split('**');
      const textElements = parts.map((part, pIdx) => {
        const isBold = pIdx % 2 === 1;
        return (
          <Text key={pIdx} style={isBold ? styles.boldText : undefined}>
            {part}
          </Text>
        );
      });

      return (
        <View key={idx} style={isBullet ? styles.bulletLine : styles.paraLine}>
          {isBullet && <Text style={styles.bulletDot}>• </Text>}
          <Text style={styles.messageText}>{textElements}</Text>
        </View>
      );
    });
  };

  // Selecionar conversa ativa
  const selectConversation = (id: string) => {
    setCurrentId(id);
    const selected = conversations.find(c => c.id === id);
    if (selected && selected.scope) setScope(selected.scope);
    toggleSidebar();
  };

  if (showSplash) {
    return <SplashScreen onFinish={() => setShowSplash(false)} />;
  }

  // --- TELA DE LOGIN & CONFIGURAÇÃO ---
  if (!isLogged) {
    return (
      <View style={[styles.flex, { backgroundColor: '#FCFBF8' }]}>
        <ExpoStatusBar style="dark" />
        <SafeAreaView style={styles.flex}>
          <KeyboardAvoidingView 
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            style={styles.flex}
          >
            <ScrollView contentContainerStyle={styles.loginScroll}>
              <View style={styles.loginHeader}>
                <View style={styles.logoBadge}>
                  <Text style={styles.logoBadgeText}>D</Text>
                </View>
                <Text style={styles.welcomeText}>Dehon AI</Text>
                <Text style={styles.loginDesc}>Biblioteca Teológica & Acervo Digital</Text>
              </View>

              <View style={styles.form}>
                <View style={styles.inputGroup}>
                  <Text style={styles.label}>E-MAIL</Text>
                  <TextInput 
                    style={styles.inputField} 
                    placeholder="pesquisador@dehoniano.org"
                    placeholderTextColor="#9ca3af"
                    keyboardType="email-address"
                    autoCapitalize="none"
                  />
                </View>

                <View style={styles.inputGroup}>
                  <Text style={styles.label}>SENHA</Text>
                  <TextInput 
                    style={styles.inputField} 
                    placeholder="Digite sua senha"
                    placeholderTextColor="#9ca3af"
                    secureTextEntry
                  />
                </View>

                <TouchableOpacity style={styles.loginBtn} onPress={handleLogin}>
                  <Text style={styles.loginBtnText}>Entrar no Acervo</Text>
                  <LucideChevronRight size={20} color="white" />
                </TouchableOpacity>

                <TouchableOpacity 
                  style={styles.configToggleBtn} 
                  onPress={() => setShowConfig(!showConfig)}
                >
                  <LucideSettings size={16} color="#6b7280" />
                  <Text style={styles.configToggleText}>Configuração de API</Text>
                </TouchableOpacity>

                {showConfig && (
                  <Animated.View style={styles.configBox}>
                    <View style={styles.inputGroup}>
                      <Text style={styles.label}>URL DO SERVIDOR BACKEND</Text>
                      <TextInput 
                        style={styles.inputFieldSmall} 
                        value={apiUrl}
                        onChangeText={setApiUrl}
                        placeholder="https://sua-api.com"
                        autoCapitalize="none"
                      />
                    </View>
                    <View style={styles.inputGroup}>
                      <Text style={styles.label}>CHAVE DE API (TOKEN)</Text>
                      <TextInput 
                        style={styles.inputFieldSmall} 
                        value={apiKey}
                        onChangeText={setApiKey}
                        secureTextEntry
                        placeholder="Token do Easypanel"
                        autoCapitalize="none"
                      />
                    </View>
                  </Animated.View>
                )}
              </View>
            </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </View>
    );
  }

  const activeConversation = conversations.find(c => c.id === currentId);

  // --- TELA DE CHAT PRINCIPAL ---
  return (
    <View style={[styles.flex, { backgroundColor: '#FCFBF8' }]}>
      <ExpoStatusBar style="dark" />
      <SafeAreaView style={styles.flex}>
        
        {/* HEADER */}
        <View style={styles.header}>
          <TouchableOpacity onPress={toggleSidebar} style={styles.headerBtn}>
            <LucideMenu size={24} color="#111827" />
          </TouchableOpacity>
          <View style={styles.headerTitleContainer}>
            <Text style={styles.headerTitle}>Dehon AI</Text>
            <Text style={styles.headerSub}>Teologia da Reparação</Text>
          </View>
          <TouchableOpacity onPress={startNewChat} style={styles.headerBtn}>
            <LucidePlus size={24} color="#111827" />
          </TouchableOpacity>
        </View>

        {/* TOP SCOPE CHIPS */}
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

        {/* CHAT MESSAGES */}
        <ScrollView 
          style={styles.chatScroll}
          contentContainerStyle={{ paddingBottom: 30 }}
          ref={(ref) => ref?.scrollToEnd({ animated: true })}
        >
          {!activeConversation || activeConversation.messages.length === 0 ? (
            <View style={styles.emptyContainer}>
              <View style={styles.emptyIconContainer}>
                <LucideCompass size={40} color="#9f1239" />
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
            activeConversation.messages.map((msg) => {
              const isAssistant = msg.role === 'assistant';
              const trustScore = msg.metadata?.trust_score;
              return (
                <View 
                  key={msg.id} 
                  style={[
                    styles.messageRow, 
                    isAssistant ? styles.messageRowAssistant : styles.messageRowUser
                  ]}
                >
                  <View style={[
                    styles.messageBubble,
                    isAssistant ? styles.bubbleAssistant : styles.bubbleUser
                  ]}>
                    
                    {/* Trust Score Badge */}
                    {isAssistant && trustScore !== undefined && trustScore > 0 && (
                      <View style={styles.trustBadge}>
                        <Text style={styles.trustBadgeText}>
                          CONFIANÇA TEOLÓGICA: {Math.round(trustScore * 100)}%
                        </Text>
                      </View>
                    )}

                    {isAssistant ? renderMessageContent(msg.content) : <Text style={styles.userText}>{msg.content}</Text>}
                    <Text style={isAssistant ? styles.timestampAssistant : styles.timestampUser}>
                      {msg.timestamp}
                    </Text>
                  </View>

                  {/* Citations Horizontal List */}
                  {isAssistant && msg.citations && msg.citations.length > 0 && (
                    <View style={styles.citationsSection}>
                      <View style={styles.citationsHeader}>
                        <LucideBookOpen size={14} color="#9f1239" />
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
              );
            })
          )}
        </ScrollView>

        {/* INPUT AREA */}
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
        >
          <View style={styles.inputContainer}>
            <TextInput 
              style={styles.chatInput}
              placeholder="Pergunte ao Magistério Dehoniano..."
              placeholderTextColor="#9ca3af"
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
                <ActivityIndicator size="small" color="white" />
              ) : (
                <LucideSend size={18} color="white" />
              )}
            </TouchableOpacity>
          </View>
        </KeyboardAvoidingView>

        {/* SIDEBAR (HISTORY DRAWER) */}
        {showSidebar && (
          <TouchableOpacity style={styles.sidebarOverlay} onPress={toggleSidebar} activeOpacity={1}>
            <Animated.View 
              style={[styles.sidebar, { transform: [{ translateX: sidebarAnim }] }]}
              onStartShouldSetResponder={() => true}
            >
              <View style={styles.sidebarHeader}>
                <Text style={styles.sidebarTitle}>Histórico</Text>
                <TouchableOpacity onPress={toggleSidebar}>
                  <LucideX size={20} color="#6b7280" />
                </TouchableOpacity>
              </View>

              <ScrollView style={styles.historyList}>
                {conversations.map((c) => (
                  <View key={c.id} style={styles.historyItemRow}>
                    <TouchableOpacity 
                      style={[styles.historyItem, currentId === c.id && styles.historyItemActive]}
                      onPress={() => selectConversation(c.id)}
                    >
                      <Text 
                        style={[styles.historyText, currentId === c.id && styles.historyTextActive]} 
                        numberOfLines={1}
                      >
                        {c.title}
                      </Text>
                    </TouchableOpacity>
                    <TouchableOpacity 
                      onPress={() => deleteChat(c.id)}
                      style={styles.deleteHistoryBtn}
                    >
                      <LucideX size={16} color="#f87171" />
                    </TouchableOpacity>
                  </View>
                ))}
              </ScrollView>

              <View style={styles.sidebarFooter}>
                <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
                  <LucideLogOut size={18} color="#f87171" />
                  <Text style={styles.logoutText}>Sair da Conta</Text>
                </TouchableOpacity>
              </View>
            </Animated.View>
          </TouchableOpacity>
        )}

        {/* CITATION MODAL DETAILS */}
        {selectedCitation && (
          <Modal visible={true} transparent animationType="slide">
            <View style={styles.modalOverlay}>
              <View style={styles.modalContent}>
                <View style={styles.modalHeader}>
                  <Text style={styles.modalTitle}>
                    [{selectedCitation.idx}] {selectedCitation.metadata?.title || 'Documento de Referência'}
                  </Text>
                  <TouchableOpacity onPress={() => setSelectedCitation(null)}>
                    <LucideX size={24} color="#6b7280" />
                  </TouchableOpacity>
                </View>
                
                <ScrollView style={styles.modalBody}>
                  <Text style={styles.modalMetaLabel}>Magistério Dehoniano</Text>
                  <Text style={styles.modalMetaValue}>
                    Autor: {selectedCitation.metadata?.author || 'Pe. Leão Dehon'}
                  </Text>
                  {selectedCitation.metadata?.page_number && (
                    <Text style={styles.modalMetaValue}>Página: {selectedCitation.metadata.page_number}</Text>
                  )}
                  {selectedCitation.metadata?.sigla && (
                    <View style={styles.siglaBadge}>
                      <Text style={styles.siglaBadgeText}>{selectedCitation.metadata.sigla}</Text>
                    </View>
                  )}
                  
                  <View style={styles.modalDivider} />
                  
                  <Text style={styles.modalTextContent}>{selectedCitation.content}</Text>
                </ScrollView>
              </View>
            </View>
          </Modal>
        )}

      </SafeAreaView>
    </View>
  );
}

// Estilos
const styles = StyleSheet.create({
  flex: { flex: 1 },
  boldText: { fontWeight: '800', color: '#111827' },
  paraLine: { marginBottom: 8 },
  bulletLine: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 6, paddingLeft: 8 },
  bulletDot: { fontSize: 16, color: '#9f1239', lineHeight: 20 },
  messageText: { fontSize: 15, color: '#374151', lineHeight: 22, fontFamily: Platform.OS === 'ios' ? 'Lora' : 'sans-serif' },
  userText: { fontSize: 16, color: '#fff', lineHeight: 22 },

  // Splash Screen
  splashContainer: {
    flex: 1,
    backgroundColor: '#FCFBF8',
    alignItems: 'center',
    justifyContent: 'center',
  },
  splashContent: {
    alignItems: 'center',
  },
  logoCircle: {
    width: 90,
    height: 90,
    borderRadius: 45,
    backgroundColor: '#9f1239',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
    shadowColor: '#9f1239',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  logoText: {
    color: '#FCFBF8',
    fontSize: 45,
    fontWeight: '800',
  },
  splashTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: '#1f2937',
    letterSpacing: 3,
  },
  splashSubtitle: {
    fontSize: 10,
    color: '#9f1239',
    letterSpacing: 4,
    marginTop: 8,
    fontWeight: '700',
  },

  // Login
  loginScroll: {
    padding: 30,
    justifyContent: 'center',
    minHeight: height - 100,
  },
  logoBadge: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#9f1239',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  logoBadgeText: {
    color: '#fff',
    fontSize: 28,
    fontWeight: '800',
  },
  loginHeader: {
    marginBottom: 40,
    alignItems: 'center',
  },
  welcomeText: {
    fontSize: 32,
    fontWeight: '800',
    color: '#1f2937',
  },
  loginDesc: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 6,
  },
  form: {
    gap: 18,
  },
  inputGroup: {
    gap: 6,
  },
  label: {
    fontSize: 10,
    fontWeight: '700',
    color: '#9f1239',
    letterSpacing: 1.5,
  },
  inputField: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 14,
    padding: 16,
    color: '#1f2937',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
  },
  inputFieldSmall: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 10,
    padding: 12,
    color: '#374151',
    fontSize: 13,
  },
  loginBtn: {
    backgroundColor: '#9f1239',
    borderRadius: 14,
    padding: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 15,
  },
  loginBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  configToggleBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 15,
  },
  configToggleText: {
    color: '#6b7280',
    fontSize: 13,
  },
  configBox: {
    marginTop: 15,
    backgroundColor: '#f3f4f6',
    borderRadius: 14,
    padding: 15,
    gap: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },

  // Main Layout
  header: {
    height: 60,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
    backgroundColor: '#FCFBF8',
  },
  headerBtn: {
    padding: 6,
  },
  headerTitleContainer: {
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
  },
  headerSub: {
    fontSize: 10,
    color: '#9f1239',
    fontWeight: '700',
    letterSpacing: 1,
  },

  // Scope Chips
  scopeContainer: {
    height: 50,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
    backgroundColor: '#FCFBF8',
  },
  scopeScroll: {
    paddingHorizontal: 15,
    alignItems: 'center',
    gap: 10,
  },
  scopeChip: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: '#f3f4f6',
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  scopeChipActive: {
    backgroundColor: '#9f1239',
    borderColor: '#9f1239',
  },
  scopeText: {
    fontSize: 13,
    color: '#4b5563',
    fontWeight: '600',
  },
  scopeTextActive: {
    color: '#FCFBF8',
  },

  // Messages Area
  chatScroll: {
    flex: 1,
    padding: 15,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
    paddingHorizontal: 20,
  },
  emptyIconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#fff1f2',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#1f2937',
    marginBottom: 8,
  },
  emptyDesc: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 30,
  },
  suggestions: {
    width: '100%',
    gap: 12,
  },
  suggestionCard: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 12,
    padding: 16,
  },
  suggestionText: {
    fontSize: 14,
    color: '#4b5563',
    fontWeight: '500',
  },

  messageRow: {
    marginVertical: 10,
    width: '100%',
  },
  messageRowUser: {
    alignItems: 'flex-end',
  },
  messageRowAssistant: {
    alignItems: 'flex-start',
  },
  messageBubble: {
    maxWidth: '85%',
    borderRadius: 18,
    padding: 15,
  },
  bubbleUser: {
    backgroundColor: '#9f1239',
    borderBottomRightRadius: 4,
  },
  bubbleAssistant: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderBottomLeftRadius: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  timestampUser: {
    fontSize: 10,
    color: '#fca5a5',
    marginTop: 6,
    alignSelf: 'flex-end',
  },
  timestampAssistant: {
    fontSize: 10,
    color: '#9ca3af',
    marginTop: 6,
    alignSelf: 'flex-start',
  },
  trustBadge: {
    backgroundColor: '#fff1f2',
    borderColor: '#ffe4e6',
    borderWidth: 1,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
    marginBottom: 10,
    alignSelf: 'flex-start',
  },
  trustBadgeText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#9f1239',
  },

  // Citations Section
  citationsSection: {
    marginTop: 10,
    width: '100%',
    paddingLeft: 10,
  },
  citationsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 6,
  },
  citationsHeaderText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#9ca3af',
    letterSpacing: 1,
  },
  citScroll: {
    paddingBottom: 4,
  },
  citCard: {
    width: 200,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 12,
    padding: 12,
    marginRight: 10,
  },
  citCardTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#9f1239',
    marginBottom: 4,
  },
  citCardText: {
    fontSize: 11,
    color: '#6b7280',
    lineHeight: 15,
  },

  // Input Section
  inputContainer: {
    flexDirection: 'row',
    padding: 15,
    backgroundColor: '#FCFBF8',
    borderTopWidth: 1,
    borderTopColor: '#f3f4f6',
    alignItems: 'center',
    gap: 10,
  },
  chatInput: {
    flex: 1,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 24,
    paddingHorizontal: 18,
    paddingVertical: 10,
    maxHeight: 100,
    color: '#1f2937',
    fontSize: 15,
  },
  sendBtn: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#9f1239',
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendBtnDisabled: {
    backgroundColor: '#e5e7eb',
  },

  // Sidebar
  sidebarOverlay: {
    position: 'absolute',
    left: 0,
    top: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.4)',
    zIndex: 999,
  },
  sidebar: {
    width: width * 0.75,
    height: '100%',
    backgroundColor: '#FCFBF8',
    borderRightWidth: 1,
    borderRightColor: '#e5e7eb',
    paddingTop: 50,
  },
  sidebarHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  sidebarTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#1f2937',
  },
  historyList: {
    flex: 1,
  },
  historyItemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 15,
    marginVertical: 4,
    justifyContent: 'space-between',
  },
  historyItem: {
    flex: 1,
    padding: 12,
    borderRadius: 10,
  },
  historyItemActive: {
    backgroundColor: '#fff1f2',
  },
  historyText: {
    fontSize: 14,
    color: '#4b5563',
    fontWeight: '600',
  },
  historyTextActive: {
    color: '#9f1239',
  },
  deleteHistoryBtn: {
    padding: 8,
  },
  sidebarFooter: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#f3f4f6',
  },
  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 12,
  },
  logoutText: {
    color: '#f87171',
    fontWeight: '700',
    fontSize: 15,
  },

  // Modal
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FCFBF8',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '85%',
    padding: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
    paddingBottom: 15,
    marginBottom: 15,
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#111827',
    maxWidth: '85%',
  },
  modalBody: {
    marginBottom: 20,
  },
  modalMetaLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: '#9f1239',
    marginBottom: 4,
  },
  modalMetaValue: {
    fontSize: 13,
    color: '#4b5563',
    marginBottom: 4,
  },
  siglaBadge: {
    backgroundColor: '#fff1f2',
    borderWidth: 1,
    borderColor: '#ffe4e6',
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 2,
    alignSelf: 'flex-start',
    marginTop: 6,
  },
  siglaBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#9f1239',
  },
  modalDivider: {
    height: 1,
    backgroundColor: '#f3f4f6',
    marginVertical: 15,
  },
  modalTextContent: {
    fontSize: 15,
    color: '#374151',
    lineHeight: 22,
  }
});
