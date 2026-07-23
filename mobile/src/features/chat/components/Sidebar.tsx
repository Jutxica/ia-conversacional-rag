import React, { useRef, useEffect } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  Animated,
  Dimensions,
  ScrollView
} from 'react-native';
import { LucideX, LucideLogOut } from 'lucide-react-native';
import { Conversation } from '../../../types/chat';
import { Colors } from '../../../theme';

const { width } = Dimensions.get('window');

interface SidebarProps {
  isVisible: boolean;
  conversations: Conversation[];
  currentId: string | null;
  onClose: () => void;
  onSelectChat: (id: string) => void;
  onDeleteChat: (id: string) => void;
  onLogout: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isVisible,
  conversations,
  currentId,
  onClose,
  onSelectChat,
  onDeleteChat,
  onLogout
}) => {
  const sidebarAnim = useRef(new Animated.Value(-width * 0.75)).current;

  useEffect(() => {
    Animated.timing(sidebarAnim, {
      toValue: isVisible ? 0 : -width * 0.75,
      duration: 250,
      useNativeDriver: false
    }).start();
  }, [isVisible]);

  if (!isVisible && sidebarAnim._value === -width * 0.75) return null;

  return (
    <TouchableOpacity
      style={styles.sidebarOverlay}
      onPress={onClose}
      activeOpacity={1}
    >
      <Animated.View
        style={[styles.sidebar, { transform: [{ translateX: sidebarAnim }] }]}
        onStartShouldSetResponder={() => true}
      >
        <View style={styles.sidebarHeader}>
          <Text style={styles.sidebarTitle}>Histórico</Text>
          <TouchableOpacity onPress={onClose}>
            <LucideX size={20} color={Colors.textTertiary} />
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.historyList}>
          {conversations.map((c) => (
            <View key={c.id} style={styles.historyItemRow}>
              <TouchableOpacity
                style={[styles.historyItem, currentId === c.id && styles.historyItemActive]}
                onPress={() => onSelectChat(c.id)}
              >
                <Text
                  style={[styles.historyText, currentId === c.id && styles.historyTextActive]}
                  numberOfLines={1}
                >
                  {c.title}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => onDeleteChat(c.id)}
                style={styles.deleteHistoryBtn}
              >
                <LucideX size={16} color={Colors.error} />
              </TouchableOpacity>
            </View>
          ))}
        </ScrollView>

        <View style={styles.sidebarFooter}>
          <TouchableOpacity style={styles.logoutBtn} onPress={onLogout}>
            <LucideLogOut size={18} color={Colors.error} />
            <Text style={styles.logoutText}>Sair da Conta</Text>
          </TouchableOpacity>
        </View>
      </Animated.View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
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
    backgroundColor: Colors.background,
    borderRightWidth: 1,
    borderRightColor: Colors.border,
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
    color: Colors.textPrimary,
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
    backgroundColor: Colors.primaryLight,
  },
  historyText: {
    fontSize: 14,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  historyTextActive: {
    color: Colors.primary,
  },
  deleteHistoryBtn: {
    padding: 8,
  },
  sidebarFooter: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
  },
  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 12,
  },
  logoutText: {
    color: Colors.error,
    fontWeight: '700',
    fontSize: 15,
  },
});
