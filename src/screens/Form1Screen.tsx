import React, { useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import FormContainer from "../components/FormContainer";
import Card from "../components/Card";
import Input from "../components/Input";
import DateInput from "../components/DateInput";
import SpeciesSelector from "../components/SpeciesSelector";
import {
  Colors,
  Gradients,
  Shadow,
  Spacing,
  Typography,
} from "../constants/theme";
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
      showSuccess("Registro salvo com sucesso!");
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
          <Text style={styles.successIcon}>✓</Text>
          <Text style={styles.successBannerText}>{successMsg}</Text>
        </View>
      )}

      <FormContainer>
        <Card
          title="Identificação"
          icon="📍"
          subtitle="Parcela, árvore e plantio"
        >
          <View style={styles.row}>
            <View style={styles.col}>
              <Input
                label="Parcela *"
                value={form.parcela}
                onChangeText={handleChange("parcela")}
                keyboardType="numeric"
                placeholder="Ex: 1"
                error={getFieldError(errors, "parcela")}
              />
            </View>
            <View style={styles.col}>
              <Input
                label="Árvore *"
                value={form.arv}
                onChangeText={handleChange("arv")}
                keyboardType="numeric"
                placeholder="Ex: 12"
                error={getFieldError(errors, "arv")}
              />
            </View>
          </View>
          <View style={styles.row}>
            <View style={styles.col}>
              <Input
                label="Plantio"
                value={form.plantio}
                onChangeText={handleChange("plantio")}
                keyboardType="numeric"
                placeholder="Ano"
                error={getFieldError(errors, "plantio")}
              />
            </View>
            <View style={styles.col}>
              <DateInput
                label="Replantio"
                value={form.replantio}
                onChangeText={handleChange("replantio")}
                error={getFieldError(errors, "replantio")}
              />
            </View>
          </View>
        </Card>

        <Card title="Espécie" icon="🌿" subtitle="Nome comum da árvore">
          <SpeciesSelector
            value={form.nomeComum}
            onChange={handleChange("nomeComum")}
            error={getFieldError(errors, "nomeComum")}
          />
        </Card>

        <Card
          title="Medição"
          icon="📐"
          subtitle="Data e parâmetros dendométricos"
        >
          <DateInput
            label="Data de Medição *"
            value={form.dataMedicao}
            onChangeText={handleChange("dataMedicao")}
            error={getFieldError(errors, "dataMedicao")}
          />
          <View style={styles.row}>
            <View style={styles.col}>
              <Input
                label="DAP"
                value={form.dap}
                onChangeText={handleChange("dap")}
                keyboardType="decimal-pad"
                placeholder="0.00"
                unit="cm"
                error={getFieldError(errors, "dap")}
              />
            </View>
            <View style={styles.col}>
              <Input
                label="Hesg"
                value={form.hesg}
                onChangeText={handleChange("hesg")}
                keyboardType="decimal-pad"
                placeholder="0.00"
                unit="m"
                error={getFieldError(errors, "hesg")}
              />
            </View>
          </View>
          <View style={styles.row}>
            <View style={styles.col}>
              <Input
                label="Hesgcopa"
                value={form.hesgcopa}
                onChangeText={handleChange("hesgcopa")}
                keyboardType="decimal-pad"
                placeholder="0.00"
                unit="m"
                error={getFieldError(errors, "hesgcopa")}
              />
            </View>
            <View style={styles.col}>
              <Input
                label="Hc"
                value={form.hc}
                onChangeText={handleChange("hc")}
                keyboardType="decimal-pad"
                placeholder="0.00"
                unit="m"
                error={getFieldError(errors, "hc")}
              />
            </View>
          </View>
          <Input
            label="Ht"
            value={form.ht}
            onChangeText={handleChange("ht")}
            keyboardType="decimal-pad"
            placeholder="0.00"
            unit="m"
            error={getFieldError(errors, "ht")}
          />
        </Card>

        <Card title="Observação" icon="📝" subtitle="Anotações adicionais">
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
          activeOpacity={0.75}
        >
          <Text style={[styles.btnText, styles.btnTextOutline]}>Salvar</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.btn, styles.btnPrimary]}
          onPress={() => handleSave(true)}
          disabled={saving}
          activeOpacity={0.78}
        >
          <LinearGradient
            colors={Gradients.header}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.btnGradient}
          >
            <Text style={[styles.btnText, styles.btnTextPrimary]}>
              Salvar e Continuar
            </Text>
          </LinearGradient>
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
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: Colors.successSoft,
    borderBottomWidth: 1,
    borderBottomColor: Colors.primarySoft,
    paddingVertical: 11,
    paddingHorizontal: Spacing.paddingScreen,
  },
  successIcon: {
    fontSize: 15,
    color: Colors.primary,
    fontWeight: "700",
  },
  successBannerText: {
    color: Colors.primary,
    fontSize: 14,
    fontWeight: "600",
  },
  row: {
    flexDirection: "row",
    gap: 10,
  },
  col: {
    flex: 1,
  },
  globalError: {
    ...Typography.errorText,
    textAlign: "center",
  },
  footer: {
    flexDirection: "row",
    gap: 10,
    paddingHorizontal: Spacing.paddingScreen,
    paddingVertical: 14,
    backgroundColor: Colors.surface,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    ...Shadow.medium,
  },
  btn: {
    flex: 1,
    height: Spacing.buttonHeight,
    borderRadius: Spacing.borderRadiusInput,
    overflow: "hidden",
  },
  btnPrimary: {
    ...Shadow.small,
  },
  btnGradient: {
    flex: 1,
    alignSelf: "stretch",
    alignItems: "center",
    justifyContent: "center",
  },
  btnOutline: {
    borderWidth: 1.5,
    borderColor: Colors.primary,
    backgroundColor: Colors.surface,
    alignItems: "center",
    justifyContent: "center",
  },
  btnText: {
    fontSize: 15,
    fontWeight: "700",
    letterSpacing: 0.2,
  },
  btnTextPrimary: { color: "#FFFFFF" },
  btnTextOutline: { color: Colors.primary },
});
