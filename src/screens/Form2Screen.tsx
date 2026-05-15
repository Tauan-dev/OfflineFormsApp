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
import SpeciesSelector from "../components/SpeciesSelector";
import SelectField from "../components/SelectField";
import { Colors, Spacing, Typography } from "../constants/theme";
import {
  savePhenologyData,
  PhenologyGroupData,
} from "../services/excelService";
import { validatePhenology, getFieldError } from "../utils/validators";

// =============================================
// ESTÁGIOS POR GRUPO
// =============================================
const FLORES_STAGES = ["botão", "em abertura", "plena floração", "senescente"];
const FRUTOS_STAGES = ["em desenvolvimento", "maduro", "senescente", "no chão"];
const FOLHAS_STAGES = ["jovens", "adultas", "senescentes"];
const NAO_APLICAVEL = "não aplicável";

function emptyGroup(stages: string[]): PhenologyGroupData {
  return { presenca: true, intensidade: "", estagio: stages[0] };
}

// =============================================
// SUB-COMPONENTE: Grupo Fenológico
// =============================================
interface GroupProps {
  title: string;
  stages: string[];
  data: PhenologyGroupData;
  onChange: (data: PhenologyGroupData) => void;
  intensidadeError?: string;
}

function PhenologyGroup({
  title,
  stages,
  data,
  onChange,
  intensidadeError,
}: GroupProps) {
  const handlePresenca = (val: boolean) => {
    if (!val) {
      onChange({ presenca: false, intensidade: "0", estagio: NAO_APLICAVEL });
    } else {
      onChange({ presenca: true, intensidade: "", estagio: stages[0] });
    }
  };

  return (
    <Card title={title}>
      {/* Presença */}
      <View style={styles.fieldGroup}>
        <Text style={styles.fieldLabel}>Presença</Text>
        <View style={styles.toggleRow}>
          <TouchableOpacity
            style={[styles.toggleBtn, data.presenca && styles.toggleActive]}
            onPress={() => handlePresenca(true)}
            activeOpacity={0.8}
          >
            <Text
              style={[
                styles.toggleText,
                data.presenca && styles.toggleTextActive,
              ]}
            >
              Sim
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.toggleBtn, !data.presenca && styles.toggleActiveNo]}
            onPress={() => handlePresenca(false)}
            activeOpacity={0.8}
          >
            <Text
              style={[
                styles.toggleText,
                !data.presenca && styles.toggleTextActive,
              ]}
            >
              Não
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Intensidade */}
      <Input
        label="Intensidade (%)"
        value={data.intensidade}
        onChangeText={(v) => onChange({ ...data, intensidade: v })}
        keyboardType="decimal-pad"
        placeholder="0 – 100"
        editable={data.presenca}
        error={intensidadeError}
      />

      {/* Estágio */}
      <SelectField
        label="Estágio"
        options={data.presenca ? stages : [NAO_APLICAVEL]}
        value={data.estagio}
        onChange={(v) => onChange({ ...data, estagio: v })}
        disabled={!data.presenca}
      />
    </Card>
  );
}

// =============================================
// TELA PRINCIPAL
// =============================================
interface Form {
  parcela: string;
  arv: string;
  nomeComum: string;
  flores: PhenologyGroupData;
  frutos: PhenologyGroupData;
  folhas: PhenologyGroupData;
}

const initialForm: Form = {
  parcela: "",
  arv: "",
  nomeComum: "",
  flores: emptyGroup(FLORES_STAGES),
  frutos: emptyGroup(FRUTOS_STAGES),
  folhas: emptyGroup(FOLHAS_STAGES),
};

export default function Form2Screen() {
  const [form, setForm] = useState<Form>(initialForm);
  const [errors, setErrors] = useState<{ field: string; message: string }[]>(
    [],
  );
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  function showSuccess(msg: string) {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(""), 3000);
  }

  async function handleSave(continueAfter = false) {
    const validationErrors = validatePhenology(form);
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }
    setErrors([]);
    setSaving(true);
    try {
      await savePhenologyData(form);
      showSuccess("Dados salvos com sucesso!");
      if (continueAfter) {
        setForm((prev) => ({
          ...initialForm,
          parcela: prev.parcela,
        }));
      } else {
        setForm(initialForm);
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
      {/* Banner de sucesso */}
      {!!successMsg && (
        <View style={styles.successBanner}>
          <Text style={styles.successBannerText}>✓ {successMsg}</Text>
        </View>
      )}

      <FormContainer>
        {/* CARD 1 — Identificação */}
        <Card title="Identificação">
          <Input
            label="Parcela"
            value={form.parcela}
            onChangeText={(v) => setForm((p) => ({ ...p, parcela: v }))}
            keyboardType="numeric"
            placeholder="Ex: 1"
            error={getFieldError(errors, "parcela")}
          />
          <Input
            label="Árvore"
            value={form.arv}
            onChangeText={(v) => setForm((p) => ({ ...p, arv: v }))}
            keyboardType="numeric"
            placeholder="Ex: 12"
            error={getFieldError(errors, "arv")}
          />
          <SpeciesSelector
            value={form.nomeComum}
            onChange={(v) => setForm((p) => ({ ...p, nomeComum: v }))}
            error={getFieldError(errors, "nomeComum")}
          />
        </Card>

        {/* CARD 2 — Flores */}
        <PhenologyGroup
          title="Flores"
          stages={FLORES_STAGES}
          data={form.flores}
          onChange={(v) => setForm((p) => ({ ...p, flores: v }))}
          intensidadeError={getFieldError(errors, "flores.intensidade")}
        />

        {/* CARD 3 — Frutos */}
        <PhenologyGroup
          title="Frutos"
          stages={FRUTOS_STAGES}
          data={form.frutos}
          onChange={(v) => setForm((p) => ({ ...p, frutos: v }))}
          intensidadeError={getFieldError(errors, "frutos.intensidade")}
        />

        {/* CARD 4 — Folhas */}
        <PhenologyGroup
          title="Folhas"
          stages={FOLHAS_STAGES}
          data={form.folhas}
          onChange={(v) => setForm((p) => ({ ...p, folhas: v }))}
          intensidadeError={getFieldError(errors, "folhas.intensidade")}
        />

        {/* Erro global */}
        {getFieldError(errors, "_global") && (
          <Text style={styles.globalError}>
            {getFieldError(errors, "_global")}
          </Text>
        )}
      </FormContainer>

      {/* Botões fixos */}
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
    flexDirection: "row",
    alignItems: "center",
  },
  successBannerText: {
    color: Colors.primary,
    fontSize: 14,
    fontWeight: "600",
  },
  fieldGroup: {
    marginBottom: 10,
  },
  fieldLabel: {
    ...Typography.label,
  },
  toggleRow: {
    flexDirection: "row",
    gap: 10,
    marginTop: 4,
  },
  toggleBtn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: Spacing.borderRadiusInput,
    borderWidth: 1.5,
    borderColor: Colors.border,
    backgroundColor: Colors.surface,
    alignItems: "center",
  },
  toggleActive: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
  },
  toggleActiveNo: {
    backgroundColor: Colors.error,
    borderColor: Colors.error,
  },
  toggleText: {
    fontSize: 15,
    fontWeight: "600",
    color: Colors.textPrimary,
  },
  toggleTextActive: {
    color: Colors.surface,
  },
  globalError: {
    ...Typography.errorText,
    textAlign: "center",
    marginTop: 4,
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
