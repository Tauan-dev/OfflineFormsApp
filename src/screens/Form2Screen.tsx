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
import SpeciesSelector from "../components/SpeciesSelector";
import SelectField from "../components/SelectField";
import {
  Colors,
  Gradients,
  Shadow,
  Spacing,
  Typography,
} from "../constants/theme";
import {
  savePhenologyData,
  PhenologyGroupData,
} from "../services/excelService";
import { validatePhenology, getFieldError } from "../utils/validators";

const FLORES_STAGES = ["botão", "em abertura", "plena floração", "senescente"];
const FRUTOS_STAGES = ["em desenvolvimento", "maduro", "senescente", "no chão"];
const FOLHAS_STAGES = ["jovens", "adultas", "senescentes"];
const NAO_APLICAVEL = "não aplicável";

function emptyGroup(stages: string[]): PhenologyGroupData {
  return { presenca: true, intensidade: "", estagio: stages[0] };
}

// ── Segmented Control (Sim | Não) ──────────────────────────────────────────
interface SegmentedProps {
  value: boolean;
  onChange: (v: boolean) => void;
}

function PresencaToggle({ value, onChange }: SegmentedProps) {
  return (
    <View style={toggle.wrap}>
      <TouchableOpacity
        style={[toggle.seg, value && toggle.segActiveYes]}
        onPress={() => onChange(true)}
        activeOpacity={0.75}
      >
        <Text style={[toggle.segText, value && toggle.segTextActive]}>Sim</Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[toggle.seg, !value && toggle.segActiveNo]}
        onPress={() => onChange(false)}
        activeOpacity={0.75}
      >
        <Text style={[toggle.segText, !value && toggle.segTextActive]}>
          Não
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const toggle = StyleSheet.create({
  wrap: {
    flexDirection: "row",
    borderRadius: Spacing.borderRadiusInput,
    borderWidth: 1,
    borderColor: "rgba(45,106,79,0.18)",
    overflow: "hidden",
    marginBottom: 14,
    alignSelf: "flex-start",
    minWidth: 168,
    backgroundColor: Colors.surfaceAlt,
    shadowColor: "#0D2B1E",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
  },
  seg: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 26,
    alignItems: "center",
    backgroundColor: "transparent",
  },
  segActiveYes: {
    backgroundColor: Colors.primary,
    shadowColor: Colors.primaryDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 2,
  },
  segActiveNo: {
    backgroundColor: Colors.error,
  },
  segText: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.textTertiary,
    letterSpacing: 0.2,
  },
  segTextActive: {
    color: "#FFFFFF",
    fontWeight: "700",
  },
});

// ── Grupo Fenológico ────────────────────────────────────────────────────────
interface GroupProps {
  title: string;
  icon: string;
  subtitle: string;
  stages: string[];
  data: PhenologyGroupData;
  onChange: (data: PhenologyGroupData) => void;
  intensidadeError?: string;
}

function PhenologyGroup({
  title,
  icon,
  subtitle,
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
    <Card title={title} icon={icon} subtitle={subtitle}>
      <Text style={groupStyles.fieldLabel}>Presença</Text>
      <PresencaToggle value={data.presenca} onChange={handlePresenca} />

      <Input
        label="Intensidade"
        value={data.intensidade}
        onChangeText={(v) => onChange({ ...data, intensidade: v })}
        keyboardType="decimal-pad"
        placeholder="0 – 100"
        unit="%"
        editable={data.presenca}
        error={intensidadeError}
      />

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

const groupStyles = StyleSheet.create({
  fieldLabel: { ...Typography.label },
});

// ── Tela principal ────────────────────────────────────────────────────────
const FITOSSANITARIO_OPTIONS = ["vivo", "morto", "com dano"];

interface Form {
  parcela: string;
  arv: string;
  nomeComum: string;
  flores: PhenologyGroupData;
  frutos: PhenologyGroupData;
  folhas: PhenologyGroupData;
  fitossanitario: string;
  observacao: string;
}

const initialForm: Form = {
  parcela: "",
  arv: "",
  nomeComum: "",
  flores: emptyGroup(FLORES_STAGES),
  frutos: emptyGroup(FRUTOS_STAGES),
  folhas: emptyGroup(FOLHAS_STAGES),
  fitossanitario: "",
  observacao: "",
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
      showSuccess("Registro salvo com sucesso!");
      if (continueAfter) {
        setForm((prev) => ({ ...initialForm, parcela: prev.parcela }));
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
      {!!successMsg && (
        <View style={styles.successBanner}>
          <Text style={styles.successIcon}>✓</Text>
          <Text style={styles.successBannerText}>{successMsg}</Text>
        </View>
      )}

      <FormContainer>
        <Card title="Identificação" icon="📍" subtitle="Parcela e árvore">
          <View style={styles.row}>
            <View style={styles.col}>
              <Input
                label="Parcela *"
                value={form.parcela}
                onChangeText={(v) => setForm((p) => ({ ...p, parcela: v }))}
                keyboardType="numeric"
                placeholder="Ex: 1"
                error={getFieldError(errors, "parcela")}
              />
            </View>
            <View style={styles.col}>
              <Input
                label="Árvore *"
                value={form.arv}
                onChangeText={(v) => setForm((p) => ({ ...p, arv: v }))}
                keyboardType="numeric"
                placeholder="Ex: 12"
                error={getFieldError(errors, "arv")}
              />
            </View>
          </View>
          <SpeciesSelector
            value={form.nomeComum}
            onChange={(v) => setForm((p) => ({ ...p, nomeComum: v }))}
            error={getFieldError(errors, "nomeComum")}
          />
        </Card>

        <PhenologyGroup
          title="Flores"
          icon="🌸"
          subtitle="Estado fenológico floral"
          stages={FLORES_STAGES}
          data={form.flores}
          onChange={(v) => setForm((p) => ({ ...p, flores: v }))}
          intensidadeError={getFieldError(errors, "flores.intensidade")}
        />

        <PhenologyGroup
          title="Frutos"
          icon="🌱"
          subtitle="Estado fenológico dos frutos"
          stages={FRUTOS_STAGES}
          data={form.frutos}
          onChange={(v) => setForm((p) => ({ ...p, frutos: v }))}
          intensidadeError={getFieldError(errors, "frutos.intensidade")}
        />

        <PhenologyGroup
          title="Folhas"
          icon="🍃"
          subtitle="Estado fenológico foliar"
          stages={FOLHAS_STAGES}
          data={form.folhas}
          onChange={(v) => setForm((p) => ({ ...p, folhas: v }))}
          intensidadeError={getFieldError(errors, "folhas.intensidade")}
        />

        <Card
          title="Estado Fitossanitário"
          icon="🌿"
          subtitle="Condição geral da árvore"
        >
          <SelectField
            label="Estado *"
            options={FITOSSANITARIO_OPTIONS}
            value={form.fitossanitario}
            onChange={(v) => setForm((p) => ({ ...p, fitossanitario: v }))}
          />
        </Card>

        <Card title="Observações" icon="📝" subtitle="Anotações adicionais">
          <Input
            label="Observações"
            value={form.observacao}
            onChangeText={(v) => setForm((p) => ({ ...p, observacao: v }))}
            placeholder="Ex: galhos quebrados, ataque de praga..."
            multiline
            numberOfLines={3}
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
  row: { flexDirection: "row", gap: 10 },
  col: { flex: 1 },
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
  btnText: { fontSize: 15, fontWeight: "700", letterSpacing: 0.2 },
  btnTextPrimary: { color: "#FFFFFF" },
  btnTextOutline: { color: Colors.primary },
});
