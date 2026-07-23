import React from 'react';
import { StyleSheet, View, Text, ActivityIndicator, Platform } from 'react-native';
import { Message } from '../../../types/chat';
import { Colors } from '../../../theme';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isAssistant = message.role === 'assistant';
  const trustScore = message.metadata?.trust_score;

  const renderContent = (text: string) => {
    if (!text && isAssistant) return <ActivityIndicator size="small" color={Colors.primary} />;

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

  return (
    <View style={[styles.messageRow, isAssistant ? styles.messageRowAssistant : styles.messageRowUser]}>
      <View style={[styles.messageBubble, isAssistant ? styles.bubbleAssistant : styles.bubbleUser]}>
        {isAssistant && trustScore !== undefined && trustScore > 0 && (
          <View style={styles.trustBadge}>
            <Text style={styles.trustBadgeText}>
              CONFIANÇA TEOLÓGICA: {Math.round(trustScore * 100)}%
            </Text>
          </View>
        )}

        {isAssistant ? (
          renderContent(message.content)
        ) : (
          <Text style={styles.userText}>{message.content}</Text>
        )}

        <Text style={isAssistant ? styles.timestampAssistant : styles.timestampUser}>
          {message.timestamp}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
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
    backgroundColor: Colors.primary,
    borderBottomRightRadius: 4,
  },
  bubbleAssistant: {
    backgroundColor: Colors.white,
    borderWidth: 1,
    borderColor: Colors.border,
    borderBottomLeftRadius: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  userText: {
    fontSize: 16,
    color: Colors.white,
    lineHeight: 22,
  },
  messageText: {
    fontSize: 15,
    color: Colors.textSecondary,
    lineHeight: 22,
    fontFamily: Platform.OS === 'ios' ? 'Lora' : 'serif',
  },
  boldText: {
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  paraLine: {
    marginBottom: 8,
  },
  bulletLine: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 6,
    paddingLeft: 8,
  },
  bulletDot: {
    fontSize: 16,
    color: Colors.primary,
    lineHeight: 20,
  },
  timestampUser: {
    fontSize: 10,
    color: '#fca5a5',
    marginTop: 6,
    alignSelf: 'flex-end',
  },
  timestampAssistant: {
    fontSize: 10,
    color: Colors.textLight,
    marginTop: 6,
    alignSelf: 'flex-start',
  },
  trustBadge: {
    backgroundColor: Colors.primaryLight,
    borderColor: Colors.primaryBorder,
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
    color: Colors.primary,
  },
});
