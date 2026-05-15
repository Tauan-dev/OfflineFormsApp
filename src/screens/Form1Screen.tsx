import React, { useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import FormContainer from "../components/FormContainer";
import Card from "../components/Card";
import Input from "../components/Input";
import DateInput from "../components/DateInput";
import SpeciesSelector from "../components/SpeciesSelector";
import { Colors, Spacing, Typography } from "../constants/theme";
import { saveDendrometryData, DendrometryData } from "../services/excelService";
import { validateDendrometry, getFieldError } from "../utils/validators";

function getTodayString(): string {
  const today = new Date();
  const d = String(today.getDate()).padStart(2, "0");
  const m = String(today.getMonth() + 1).padStart(2, "0");
  const y = today.getFullYear();
  return `${d}/${m}/${y}`;
}

const initialState: DendrometryData = {
  parcela: "",
  arv: "",
  plantio: "",
  replantio: "",
  nomeComum: "",
  dataMedicao: getTodayString(),
  dap: "",
  hesg: "",
  hesgcopa: "",
  hc: "",
  ht: "",
  observacao: "",
};

export default function Form1Screen() {
  const [form, setForm] = useState<DendrometryData>(initialState);
  const [errors, setErrors] = useState<{ field: string; message: string }[]>(
    [],
  );
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  function handleChange(field: keyof DendrometryData) {
    return (value: string) => setForm((prev) => ({ ...prev, [field]: value }));
  }

  function showSuccess(msg: string) {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(""), 3000);
  }

  async function handleSave(continueAfter = false) {
    const validationErrors = validateDendrometry(form);
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }
    setErrors([]);
    setSaving(true);
    try {
      await saveDendrometryData(form);
      showSuccess("Dados salvos com sucesso!");
      if (continueAfter) {
        setForm((prev) => ({
          ...initialState,
          parcela: prev.parcela,
          dataMedicao: prev.dataMedicao,
        }));
      } else {
        setForm(initialState);
      }
    } catch {
      setErrors([
        { field: "_global", message: "Erro ao salvar. Tente novamente." },
      ]);
    } finally {
      setSaving(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.wrapper}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      {!!successMsg && (
        <View style={styles.successBanner}>
          <Text style={styles.successBannerText}>✓ {successMsg}</Text>
        </View>
      )}

      <FormContainer>
        <Card title="Identificação">
          <Input
            label="Parcela *"
            value={form.parcela}
            onChangeText={handleChange("parcela")}
            keyboardType="numeric"
            placeholder="Ex: 1"
            error={getFieldError(errors, "parcela")}
          />
          <Input
            label="Árvore *"
            value={form.arv}
            onChangeText={handleChange("arv")}
            keyboardType="numeric"
            placeholder="Ex: 12"
            error={getFieldError(errors, "arv")}
          />
          <Input
            label="Plantio"
            value={form.plantio}
            onChangeText={handleChange("plantio")}
            keyboardType="numeric"
            placeholder="Ex: 2020"
          />
          <DateInput
            label="Replantio (data)"
            value={form.replantio}
            onChangeText={handleChange("replantio")}
          />
        </Card>

        <Card title="Espécie">
          <SpeciesSelector
            value={form.nomeComum}
            onChange={handleChange("nomeComum")}
            error={getFieldError(errors, "nomeComum")}
          />
        </Card>

        <Card title="Medições">
          <DateInput
            label="Data de Medição *"
            value={form.dataMedicao}
            onChangeText={handleChange("dataMedicao")}
            error={getFieldError(errors, "dataMedicao")}
          />
          <Input
            label="DAP (cm)"
            value={form.dap}
            onChangeText={handleChange("dap")}
            keyboardType="decimal-pad"
            placeholder="0.00"
            error={getFieldError(errors, "dap")}
          />
          <Input
            label="Hesg (m)"
            value={form.hesg}
            onChangeText={handleChange("hesg")}
            keyboardType="decimal-pad"
            placeholder="0.00"
            error={getFieldError(errors, "hesg")}
          />
          <Input
            label="Hesgcopa (m)"
            value={form.hesgcopa}
            onChangeText={handleChange("hesgcopa")}
            keyboardType="decimal-pad"
            placeholder="0.00"
            error={getFieldError(errors, "hesgcopa")}
          />
          <Input
            label="Hc (m)"
            value={form.hc}
            onChangeText={handleChange("hc")}
            keyboardType="decimal-pad"
            placeholder="0.00"
            error={getFieldError(errors, "hc")}
          />
          <Input
            label="Ht (m)"
            value={form.ht}
            onChangeText={handleChange("ht")}
            keyboardType="decimal-pad"
            placeholder="0.00"
            error={getFieldError(errors, "ht")}
          />
        </Card>

        <Card title="Observação">
          <Input
            label="Observação"
            value={form.observacao}
            onChangeText={handleChange("observacao")}
            multiline
            numberOfLines={4}
            placeholder="Anotações adicionais..."
          />
        </Card>

        {getFieldError(errors, "_global") && (
          <Text style={styles.globalError}>
            {getFieldError(errors, "_global")}
          </Text>
        )}
      </FormContainer>

      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.btn, styles.btnOutline]}
          onPress={() => handleSave(false)}
          disabled={saving}
        >
          <Text style={[styles.btnText, styles.btnTextOutline]}>Salvar</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.btn, styles.btnPrimary]}
          onPress={() => handleSave(true)}
          disabled={saving}
        >
          <Text style={[styles.btnText, styles.btnTextPrimary]}>
            Salvar e Continuar
          </Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  successBanner: {
    backgroundColor: Colors.successSoft,
    borderBottomWidth: 1,
    borderBottomColor: Colors.primarySoft,
    paddingVertical: 10,
    paddingHorizontal: Spacing.paddingScreen,
  },
  successBannerText: {
    color: Colors.primary,
    fontSize: 14,
    fontWeight: "600",
  },
  globalError: {
    ...Typography.errorText,
    textAlign: "center",
  },
  footer: {
    flexDirection: "row",
    gap: 10,
    paddingHorizontal: Spacing.paddingScreen,
    paddingVertical: 12,
    backgroundColor: Colors.surface,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  btn: {
    flex: 1,
    height: Spacing.buttonHeight,
    borderRadius: Spacing.borderRadiusInput,
    alignItems: "center",
    justifyContent: "center",
  },
  btnPrimary: {
    backgroundColor: Colors.primary,
  },
  btnOutline: {
    borderWidth: 1.5,
    borderColor: Colors.primary,
    backgroundColor: Colors.surface,
  },
  btnText: {
    fontSize: 15,
    fontWeight: "600",
  },
  btnTextPrimary: {
    color: Colors.surface,
  },
  btnTextOutline: {
    color: Colors.primary,
  },
});
