import React, { useEffect, useState, useCallback, useRef } from "react";
import {
  View,
  Text,
  TextInput,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Modal,
  Dimensions,
} from "react-native";
import { Colors, Spacing, Typography, Shadow } from "../constants/theme";
import { getSpeciesList, addNewSpecies } from "../storage/speciesStorage";

const SCREEN_H = Dimensions.get("window").height;
const DROPDOWN_MAX_H = 220;

interface SpeciesSelectorProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

export default function SpeciesSelector({
  value,
  onChange,
  error,
}: SpeciesSelectorProps) {
  const [query, setQuery] = useState(value);
  const [species, setSpecies] = useState<string[]>([]);
  const [filtered, setFiltered] = useState<string[]>([]);
  const [showList, setShowList] = useState(false);
  const [dropdownPos, setDropdownPos] = useState({
    x: 0,
    y: 0,
    width: 0,
    openUp: false,
  });

  const inputRef = useRef<View>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    loadSpecies();
  }, []);
  useEffect(() => {
    setQuery(value);
  }, [value]);

  const loadSpecies = async () => {
    const list = await getSpeciesList();
    setSpecies(list);
  };

  /** Mede a posição real do input na tela e abre o dropdown */
  const openDropdown = useCallback(
    (currentSpecies: string[], currentQuery: string) => {
      inputRef.current?.measure((_fx, _fy, width, height, px, py) => {
        const spaceBelow = SCREEN_H - (py + height);
        const openUp = spaceBelow < DROPDOWN_MAX_H + 10;
        setDropdownPos({ x: px, y: py + height, width, openUp });
        const q = currentQuery.trim();
        if (q.length > 0) {
          setFiltered(
            currentSpecies.filter((s) =>
              s.toLowerCase().includes(q.toLowerCase()),
            ),
          );
        } else {
          setFiltered(currentSpecies);
        }
        setShowList(true);
      });
    },
    [],
  );

  const handleFocus = useCallback(() => {
    openDropdown(species, query);
  }, [species, query, openDropdown]);

  const handleChangeText = useCallback(
    (text: string) => {
      setQuery(text);

      // cancela qualquer atualização pendente do dropdown
      if (debounceRef.current) clearTimeout(debounceRef.current);

      debounceRef.current = setTimeout(() => {
        if (text.length > 0) {
          const f = species.filter((s) =>
            s.toLowerCase().includes(text.toLowerCase()),
          );
          setFiltered(f);
        } else {
          setFiltered(species);
          onChange("");
        }
        setShowList(true);
      }, 300);
    },
    [species, onChange],
  );

  const handleSelect = (item: string) => {
    setQuery(item);
    onChange(item);
    setShowList(false);
  };

  const handleBlur = async () => {
    setTimeout(async () => {
      const trimmed = query.trim();
      setShowList(false);
      if (!trimmed) return;
      const exists = species.some(
        (s) => s.toLowerCase() === trimmed.toLowerCase(),
      );
      if (!exists) {
        await addNewSpecies(trimmed);
        await loadSpecies();
      }
      onChange(trimmed);
    }, 200);
  };

  const dropdownTop = dropdownPos.openUp
    ? dropdownPos.y - DROPDOWN_MAX_H - (Spacing.inputHeight ?? 48)
    : dropdownPos.y;

  return (
    <View ref={inputRef} collapsable={false} style={styles.container}>
      <Text style={styles.label}>Nome Comum</Text>
      <TextInput
        style={[styles.input, !!error && styles.inputError]}
        value={query}
        onChangeText={handleChangeText}
        onFocus={handleFocus}
        onBlur={handleBlur}
        placeholder="Digite ou selecione a espécie..."
        placeholderTextColor={Colors.textSecondary}
      />
      {!!error && <Text style={styles.errorText}>{error}</Text>}

      {/* hint de nova espécie — abaixo do input, sem modal */}
      {showList &&
        filtered.length === 0 &&
        query.trim().length > 0 &&
        species.length > 0 && (
          <View style={styles.newTag}>
            <Text style={styles.newTagText}>
              ✚ Nova espécie: "{query.trim()}" (será salva ao confirmar)
            </Text>
          </View>
        )}

      {/* Dropdown renderizado sobre TUDO via Modal transparente */}
      <Modal
        visible={showList && filtered.length > 0}
        transparent
        animationType="none"
        onRequestClose={() => setShowList(false)}
      >
        {/* área de toque fora fecha o dropdown */}
        <TouchableOpacity
          style={StyleSheet.absoluteFill}
          activeOpacity={1}
          onPress={() => setShowList(false)}
        />
        <View
          style={[
            styles.dropdown,
            {
              position: "absolute",
              top: dropdownTop,
              left: dropdownPos.x,
              width: dropdownPos.width,
            },
          ]}
        >
          <ScrollView
            keyboardShouldPersistTaps="handled"
            style={{ maxHeight: DROPDOWN_MAX_H }}
            nestedScrollEnabled
          >
            {filtered.map((item) => (
              <TouchableOpacity
                key={item}
                style={styles.item}
                onPress={() => handleSelect(item)}
              >
                <Text style={styles.itemText}>{item}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 14,
  },
  label: {
    ...Typography.label,
  },
  input: {
    height: Spacing.inputHeight,
    borderWidth: 1,
    borderColor: "rgba(45,106,79,0.18)",
    borderRadius: Spacing.borderRadiusInput,
    paddingHorizontal: 14,
    fontSize: 16,
    color: Colors.textPrimary,
    backgroundColor: Colors.surface,
    shadowColor: "#0D2B1E",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 1,
  },
  inputError: {
    borderColor: Colors.error,
    borderWidth: 1.5,
    backgroundColor: Colors.errorSoft,
  },
  errorText: {
    ...Typography.errorText,
  },
  dropdown: {
    backgroundColor: Colors.surface,
    borderWidth: 0.5,
    borderColor: "rgba(45,106,79,0.12)",
    borderRadius: Spacing.borderRadius,
    shadowColor: "#0D2B1E",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.16,
    shadowRadius: 20,
    elevation: 10,
    overflow: "hidden",
  },
  item: {
    paddingHorizontal: 16,
    paddingVertical: 13,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(45,106,79,0.06)",
  },
  itemText: {
    fontSize: 15,
    color: Colors.textPrimary,
    letterSpacing: 0.1,
  },
  newTag: {
    marginTop: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: Colors.successSoft,
    borderRadius: Spacing.borderRadiusInput,
    borderWidth: 1,
    borderColor: Colors.primarySoft,
  },
  newTagText: {
    fontSize: 12,
    color: Colors.primary,
    fontWeight: "600",
  },
});
