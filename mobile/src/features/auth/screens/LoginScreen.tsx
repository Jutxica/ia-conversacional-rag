import React, { useState } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Dimensions,
  Animated
} from 'react-native';
import { LucideChevronRight, LucideSettings } from 'lucide-react-native';
import { Colors } from '../../../theme';

const { height } = Dimensions.get('window');

interface LoginScreenProps {
  apiUrl: string;
  apiKey: string;
  onLogin: (apiUrl: string, apiKey: string) => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({
  apiUrl: initialApiUrl,
  apiKey: initialApiKey,
  onLogin
}) => {
  const [apiUrl, setApiUrl] = useState(initialApiUrl);
  const [apiKey, setApiKey] = useState(initialApiKey);
  const [showConfig, setShowConfig] = useState(false);

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
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
              placeholderTextColor={Colors.textLight}
              keyboardType="email-address"
              autoCapitalize="none"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>SENHA</Text>
            <TextInput
              style={styles.inputField}
              placeholder="Digite sua senha"
              placeholderTextColor={Colors.textLight}
              secureTextEntry
            />
          </View>

          <TouchableOpacity
            style={styles.loginBtn}
            onPress={() => onLogin(apiUrl, apiKey)}
          >
            <Text style={styles.loginBtnText}>Entrar no Acervo</Text>
            <LucideChevronRight size={20} color={Colors.white} />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.configToggleBtn}
            onPress={() => setShowConfig(!showConfig)}
          >
            <LucideSettings size={16} color={Colors.textTertiary} />
            <Text style={styles.configToggleText}>Configuração de API</Text>
          </TouchableOpacity>

          {showConfig && (
            <View style={styles.configBox}>
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
            </View>
          )}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  loginScroll: {
    padding: 30,
    justifyContent: 'center',
    minHeight: height - 100,
  },
  loginHeader: {
    marginBottom: 40,
    alignItems: 'center',
  },
  logoBadge: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  logoBadgeText: {
    color: Colors.white,
    fontSize: 28,
    fontWeight: '800',
  },
  welcomeText: {
    fontSize: 32,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  loginDesc: {
    fontSize: 14,
    color: Colors.textTertiary,
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
    color: Colors.primary,
    letterSpacing: 1.5,
  },
  inputField: {
    backgroundColor: Colors.white,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 14,
    padding: 16,
    color: Colors.textPrimary,
  },
  loginBtn: {
    backgroundColor: Colors.primary,
    borderRadius: 14,
    padding: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 15,
  },
  loginBtnText: {
    color: Colors.white,
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
    color: Colors.textTertiary,
    fontSize: 13,
  },
  configBox: {
    marginTop: 15,
    backgroundColor: Colors.borderLight,
    borderRadius: 14,
    padding: 15,
    gap: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  inputFieldSmall: {
    backgroundColor: Colors.white,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 10,
    padding: 12,
    color: Colors.textSecondary,
    fontSize: 13,
  },
});
