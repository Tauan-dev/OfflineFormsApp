import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  KeyboardTypeOptions,
} from "react-native";
import { Colors, Spacing, Typography } from "../constants/theme";

interface InputProps {
  label: string;
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  keyboardType?: KeyboardTypeOptions;
  multiline?: boolean;
  numberOfLines?: number;
  editable?: boolean;
  error?: string;
  unit?: string;
}

export default function Input({
  label,
  value,
  onChangeText,
  placeholder,
  keyboardType = "default",
  multiline = false,
  numberOfLines = 1,
  editable = true,
  error,
  unit,
}: InputProps) {
  const [focused, setFocused] = useState(false);

  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <View
        style={[
          styles.inputWrapper,
          multiline && styles.inputWrapperMultiline,
          focused && styles.inputWrapperFocused,
          !editable && styles.inputWrapperDisabled,
          !!error && styles.inputWrapperError,
        ]}
      >
        <TextInput
          style={[styles.input, multiline && styles.multiline]}
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={Colors.textTertiary}
          keyboardType={keyboardType}
          multiline={multiline}
          numberOfLines={multiline ? numberOfLines : 1}
          editable={editable}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
        />
        {!!unit && (
          <Text style={[styles.unit, focused && styles.unitFocused]}>
            {unit}
          </Text>
        )}
      </View>
      {!!error && <Text style={styles.errorText}>{error}</Text>}
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
  inputWrapperMultiline: {
    height: undefined,
    paddingVertical: 12,
    alignItems: "flex-start",
  },
  inputWrapperFocused: {
    borderColor: Colors.primaryLight,
    borderWidth: 1.5,
    backgroundColor: "#FAFDFA",
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  inputWrapperDisabled: {
    backgroundColor: Colors.surfaceAlt,
    borderColor: "rgba(45,106,79,0.08)",
    shadowOpacity: 0,
    elevation: 0,
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
    letterSpacing: 0.1,
  },
  multiline: {
    height: 90,
    textAlignVertical: "top",
  },
  unit: {
    ...Typography.unit,
    marginLeft: 10,
    paddingLeft: 10,
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 6,
    backgroundColor: Colors.primaryMuted,
    color: Colors.primary,
    fontSize: 12,
    fontWeight: "700",
    overflow: "hidden",
  },
  unitFocused: {
    backgroundColor: Colors.primarySoft,
    color: Colors.primaryDark,
  },
  errorText: {
    ...Typography.errorText,
  },
});
