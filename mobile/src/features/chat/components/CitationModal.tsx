import React from 'react';
import { StyleSheet, View, Text, Modal, TouchableOpacity, ScrollView } from 'react-native';
import { LucideX } from 'lucide-react-native';
import { Citation } from '../../../types/chat';
import { Colors } from '../../../theme';

interface CitationModalProps {
  citation: (Citation & { idx: number }) | null;
  onClose: () => void;
}

export const CitationModal: React.FC<CitationModalProps> = ({ citation, onClose }) => {
  if (!citation) return null;

  return (
    <Modal visible={true} transparent animationType="slide">
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle} numberOfLines={2}>
              [{citation.idx}] {citation.metadata?.title || 'Documento de Referência'}
            </Text>
            <TouchableOpacity onPress={onClose}>
              <LucideX size={24} color={Colors.textTertiary} />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalBody}>
            <Text style={styles.modalMetaLabel}>Magistério Dehoniano</Text>
            <Text style={styles.modalMetaValue}>
              Autor: {citation.metadata?.author || 'Pe. Leão Dehon'}
            </Text>
            {citation.metadata?.page_number && (
              <Text style={styles.modalMetaValue}>Página: {citation.metadata.page_number}</Text>
            )}
            {citation.metadata?.sigla && (
              <View style={styles.siglaBadge}>
                <Text style={styles.siglaBadgeText}>{citation.metadata.sigla}</Text>
              </View>
            )}

            <View style={styles.modalDivider} />

            <Text style={styles.modalTextContent}>{citation.content}</Text>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: Colors.background,
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
    borderBottomColor: Colors.borderLight,
    paddingBottom: 15,
    marginBottom: 15,
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: Colors.textPrimary,
    maxWidth: '85%',
  },
  modalBody: {
    marginBottom: 20,
  },
  modalMetaLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.primary,
    marginBottom: 4,
  },
  modalMetaValue: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginBottom: 4,
  },
  siglaBadge: {
    backgroundColor: Colors.primaryLight,
    borderWidth: 1,
    borderColor: Colors.primaryBorder,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 2,
    alignSelf: 'flex-start',
    marginTop: 6,
  },
  siglaBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.primary,
  },
  modalDivider: {
    height: 1,
    backgroundColor: Colors.borderLight,
    marginVertical: 15,
  },
  modalTextContent: {
    fontSize: 15,
    color: Colors.textSecondary,
    lineHeight: 22,
  }
});
