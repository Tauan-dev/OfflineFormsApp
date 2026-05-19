import React, { useState } from "react";
import { View, Text, TextInput, StyleSheet } from "react-native";
import { Colors, Spacing, Typography } from "../constants/theme";

interface DateInputProps {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  placeholder?: string;
  error?: string;
}

function applyMask(raw: string): string {
  const digits = raw.replace(/\D/g, "").slice(0, 8);
  if (digits.length <= 2) return digits;
  if (digits.length <= 4) return `${digits.slice(0, 2)}/${digits.slice(2)}`;
  return `${digits.slice(0, 2)}/${digits.slice(2, 4)}/${digits.slice(4)}`;
}

export default function DateInput({
  label,
  value,
  onChangeText,
  placeholder = "DD/MM/AAAA",
  error,
}: DateInputProps) {
  const [focused, setFocused] = useState(false);

  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <View
        style={[
          styles.inputWrapper,
          focused && styles.inputWrapperFocused,
          !!error && styles.inputWrapperError,
        ]}
      >
        <TextInput
          style={styles.input}
          value={value}
          onChangeText={(t) => onChangeText(applyMask(t))}
          placeholder={placeholder}
          placeholderTextColor={Colors.textTertiary}
          keyboardType="numeric"
          maxLength={10}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
        />
      </View>
      {!!error && <Text style={styles.errorText}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginBottom: 14 },
  label: { ...Typography.label },
  inputWrapper: {
    flexDirection: "row",
    alignItems: "center",
    height: Spacing.inputHeight,
    borderWidth: 1,
    borderColor: "rgba(45,106,79,0.18)",
    borderRadius: Spacing.borderRadiusInput,
    backgroundColor: Colors.surface,
    paddingHorizontal: 14,
    shadowColor: "#0D2B1E",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 1,
  },
  inputWrapperFocused: {
    borderColor: Colors.primaryLight,
    borderWidth: 1.5,
    backgroundColor: "#FAFDFA",
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  inputWrapperError: {
    borderColor: Colors.error,
    borderWidth: 1.5,
    backgroundColor: Colors.errorSoft,
    shadowOpacity: 0,
    elevation: 0,
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: Colors.textPrimary,
    paddingVertical: 0,
    letterSpacing: 1.5,
  },
  calIcon: {
    fontSize: 15,
    opacity: 0.35,
    marginLeft: 4,
  },
  calIconFocused: { opacity: 0.75 },
  errorText: { ...Typography.errorText },
});
