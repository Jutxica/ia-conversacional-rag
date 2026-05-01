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
  Animated 
} from 'react-native';
import { LucideShieldCheck, LucideChevronRight } from 'lucide-react-native';
import { StatusBar as ExpoStatusBar } from 'expo-status-bar';

const { width } = Dimensions.get('window');

// --- Componente: Splash Screen (Usando animação nativa básica) ---
const SplashScreen = ({ onFinish }: { onFinish: () => void }) => {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.8)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        friction: 4,
        useNativeDriver: true,
      })
    ]).start();

    const timer = setTimeout(onFinish, 3000);
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

// --- Componente: Login Screen ---
const LoginScreen = () => {
  return (
    <View style={styles.loginContainer}>
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.flex}
      >
        <ScrollView contentContainerStyle={styles.loginScroll}>
          <View style={styles.loginHeader}>
            <Text style={styles.welcomeText}>Bem-vindo de volta</Text>
            <Text style={styles.loginDesc}>Acesse seu acervo de pesquisa especializado.</Text>
          </View>

          <View style={styles.form}>
            <View style={styles.inputGroup}>
              <Text style={styles.label}>E-MAIL</Text>
              <View style={styles.inputField}>
                <Text style={{color: '#9ca3af'}}>exemplo@dehon.org</Text>
              </View>
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>SENHA</Text>
              <View style={styles.inputField}>
                <Text style={{color: '#9ca3af'}}>••••••••</Text>
              </View>
            </View>

            <TouchableOpacity style={styles.loginBtn}>
              <Text style={styles.loginBtnText}>Acessar Biblioteca</Text>
              <LucideChevronRight size={20} color="white" />
            </TouchableOpacity>

            <TouchableOpacity style={styles.signupLink}>
              <Text style={styles.signupText}>
                Ainda não tem conta? <Text style={styles.signupHighlight}>Criar agora</Text>
              </Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
};

export default function App() {
  const [showSplash, setShowSplash] = useState(true);

  return (
    <View style={styles.flex}>
      <ExpoStatusBar style="dark" />
      {showSplash ? (
        <SplashScreen onFinish={() => setShowSplash(false)} />
      ) : (
        <LoginScreen />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: '#fff' },
  splashContainer: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  splashContent: {
    alignItems: 'center',
  },
  logoCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#2563eb',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
    elevation: 10,
  },
  logoText: {
    color: '#fff',
    fontSize: 50,
    fontWeight: '800',
  },
  splashTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: '#111827',
    letterSpacing: 2,
  },
  splashSubtitle: {
    fontSize: 12,
    color: '#6b7280',
    letterSpacing: 4,
    marginTop: 8,
    fontWeight: '600',
  },
  loginContainer: {
    flex: 1,
    paddingTop: 60,
  },
  loginScroll: {
    padding: 30,
  },
  loginHeader: {
    marginBottom: 40,
  },
  welcomeText: {
    fontSize: 32,
    fontWeight: '800',
    color: '#111827',
  },
  loginDesc: {
    fontSize: 16,
    color: '#6b7280',
    marginTop: 10,
  },
  form: {
    gap: 20,
  },
  inputGroup: {
    gap: 8,
  },
  label: {
    fontSize: 11,
    fontWeight: '700',
    color: '#9ca3af',
    letterSpacing: 1.5,
    marginLeft: 4,
  },
  inputField: {
    backgroundColor: '#f9fafb',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 16,
    padding: 18,
  },
  loginBtn: {
    backgroundColor: '#2563eb',
    borderRadius: 16,
    padding: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    marginTop: 20,
    elevation: 5,
  },
  loginBtnText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
  },
  signupLink: {
    marginTop: 25,
    alignItems: 'center',
  },
  signupText: {
    color: '#6b7280',
    fontSize: 14,
  },
  signupHighlight: {
    color: '#2563eb',
    fontWeight: '700',
  }
});
