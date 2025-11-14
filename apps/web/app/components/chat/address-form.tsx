import { useState, useEffect } from "react";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { ScrollArea } from "~/components/ui/scroll-area";

// DIPOMEX API interfaces
interface Estado {
  ESTADO_ID: string;
  ESTADO: string;
  EDO1: string;
  RANGO1: string;
  RANGO2: string;
}

interface Municipio {
  ESTADO_ID: string;
  MUNICIPIO_ID: string;
  MUNICIPIO: string;
  RANGO1: string;
  RANGO2: string;
}

// Colonia interface no longer needed since we use CP search

interface CodigoPostalResponse {
  error: boolean;
  message: string;
  codigo_postal: {
    estado: string;
    estado_abreviatura: string;
    municipio: string;
    centro_reparto: string;
    codigo_postal: string;
    colonias: string[];
  };
}

interface EstadosResponse {
  error: boolean;
  message: string;
  estados: Estado[];
}

interface MunicipiosResponse {
  error: boolean;
  message: string;
  municipios: Municipio[];
}

// ColoniasResponse no longer needed since we use CP search

interface AddressData {
  street: string;
  exteriorNumber?: string;
  interiorNumber?: string;
  neighborhood: string;
  postalCode: string;
  municipality: string;
  state: string;
}

interface AddressFormProps {
  onAddressSubmit: (address: AddressData) => void;
  onCancel?: () => void;
}

export function AddressForm({ onAddressSubmit, onCancel }: AddressFormProps) {
  // Form state
  const [street, setStreet] = useState("");
  const [exteriorNumber, setExteriorNumber] = useState("");
  const [interiorNumber, setInteriorNumber] = useState("");
  const [postalCode, setPostalCode] = useState("");
  // Auto-set from CP search, kept for compatibility but not displayed
  const [selectedEstado, setSelectedEstado] = useState("");
  const [selectedMunicipio, setSelectedMunicipio] = useState("");
  const [selectedColonia, setSelectedColonia] = useState("");

  // DIPOMEX data
  const [estados, setEstados] = useState<Estado[]>([]);
  const [municipios, setMunicipios] = useState<Municipio[]>([]);

  // UI state
  const [isLoadingEstados, setIsLoadingEstados] = useState(false);
  const [isSearchingByCP, setIsSearchingByCP] = useState(false);
  const [cpSearchResult, setCpSearchResult] = useState<CodigoPostalResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const baseUrl = 'http://localhost:8000';

  // Load estados on component mount
  useEffect(() => {
    loadEstados();
  }, []);

  const loadEstados = async () => {
    setIsLoadingEstados(true);
    try {
      const response = await fetch(`${baseUrl}/api/v1/dipomex/estados`);
      if (response.ok) {
        const data: EstadosResponse = await response.json();
        // Extract estados array from response
        if (data.estados && Array.isArray(data.estados)) {
          setEstados(data.estados);
        } else {
          console.error('Estados response does not contain valid estados array:', data);
          setEstados([]);
        }
      } else {
        console.error('Error loading estados:', response.statusText);
        setEstados([]);
      }
    } catch (error) {
      console.error('Error loading estados:', error);
      setEstados([]);
    } finally {
      setIsLoadingEstados(false);
    }
  };

  const loadMunicipios = async (estadoId: string) => {
    setMunicipios([]);
    setSelectedMunicipio("");
    
    try {
      const response = await fetch(`${baseUrl}/api/v1/dipomex/municipios/${estadoId}`);
      if (response.ok) {
        const data: MunicipiosResponse = await response.json();
        if (data.municipios && Array.isArray(data.municipios)) {
          setMunicipios(data.municipios);
        } else {
          console.error('Municipios response does not contain valid municipios array:', data);
          setMunicipios([]);
        }
      } else {
        console.error('Error loading municipios:', response.statusText);
        setMunicipios([]);
      }
    } catch (error) {
      console.error('Error loading municipios:', error);
      setMunicipios([]);
    }
  };

  const searchByCodigoPostal = async (cp: string) => {
    if (cp.length !== 5 || !/^\d+$/.test(cp)) return;
    
    setIsSearchingByCP(true);
    setCpSearchResult(null);
    
    try {
      const response = await fetch(`${baseUrl}/api/v1/dipomex/codigo_postal/${cp}`);
      if (response.ok) {
        const data: CodigoPostalResponse = await response.json();
        setCpSearchResult(data);
      } else {
        console.error('Error searching by codigo postal:', response.statusText);
        setCpSearchResult(null);
      }
    } catch (error) {
      console.error('Error searching by codigo postal:', error);
      setCpSearchResult(null);
    } finally {
      setIsSearchingByCP(false);
    }
  };


  const handleCPSearch = (cp: string) => {
    setPostalCode(cp);
    searchByCodigoPostal(cp);
  };

  const selectFromCPResult = (coloniaName: string) => {
    if (!cpSearchResult) return;
    
    const result = cpSearchResult.codigo_postal;
    setPostalCode(result.codigo_postal);
    setSelectedColonia(coloniaName);
    
    // Auto-set estado and municipio from CP result
    const estado = estados.find(e => e.ESTADO === result.estado);
    if (estado) {
      setSelectedEstado(estado.ESTADO_ID);
      
      // Load municipios and then auto-select
      loadMunicipios(estado.ESTADO_ID).then(() => {
        setTimeout(() => {
          const municipio = municipios.find(m => m.MUNICIPIO === result.municipio);
          if (municipio) {
            setSelectedMunicipio(municipio.MUNICIPIO_ID);
          }
        }, 100);
      });
    }
    
    // Keep the search result for display but don't clear it
    // setCpSearchResult(null);
  };

  const getSelectedEstadoName = (): string => {
    if (cpSearchResult && selectedColonia) {
      return cpSearchResult.codigo_postal.estado;
    }
    const estado = estados.find(e => e.ESTADO_ID === selectedEstado);
    return estado?.ESTADO || "";
  };

  const getSelectedMunicipioName = (): string => {
    if (cpSearchResult && selectedColonia) {
      return cpSearchResult.codigo_postal.municipio;
    }
    const municipio = municipios.find(m => m.MUNICIPIO_ID === selectedMunicipio);
    return municipio?.MUNICIPIO || "";
  };

  const getSelectedColoniaName = (): string => {
    return selectedColonia || "";
  };

  const isFormValid = (): boolean => {
    return !!(
      street.trim() &&
      postalCode.trim() &&
      selectedColonia
    );
  };

  const handleSubmit = async () => {
    if (!isFormValid()) return;
    
    setIsSubmitting(true);
    
    const addressData: AddressData = {
      street: street.trim(),
      exteriorNumber: exteriorNumber.trim() || undefined,
      interiorNumber: interiorNumber.trim() || undefined,
      neighborhood: getSelectedColoniaName(),
      postalCode: postalCode.trim(),
      municipality: getSelectedMunicipioName(),
      state: getSelectedEstadoName()
    };

    // Create address message for the agent
    const addressMessage = `Mi domicilio fiscal es:
Calle: ${addressData.street}${addressData.exteriorNumber ? ` #${addressData.exteriorNumber}` : ''}${addressData.interiorNumber ? ` Int. ${addressData.interiorNumber}` : ''}
Colonia: ${addressData.neighborhood}
Código Postal: ${addressData.postalCode}
Municipio: ${addressData.municipality}
Estado: ${addressData.state}`;

    try {
      await onAddressSubmit(addressData);
    } catch (error) {
      console.error('Error submitting address:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-white/90 backdrop-blur-md border border-white/50 rounded-2xl shadow-lg">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-sky-700 mb-2">
          Domicilio Fiscal
        </h3>
        <p className="text-sm text-sky-600 mb-4">
          Proporciona tu dirección fiscal completa. Ingresa tu código postal para seleccionar tu colonia automáticamente.
        </p>
      </div>

      <div className="space-y-4">
        {/* Address fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-sky-700 mb-1">
              Calle *
            </label>
            <Input
              value={street}
              onChange={(e) => setStreet(e.target.value)}
              placeholder="Ej: Av. Insurgentes Sur"
              className="w-full"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-sky-700 mb-1">
              Número Exterior
            </label>
            <Input
              value={exteriorNumber}
              onChange={(e) => setExteriorNumber(e.target.value)}
              placeholder="123"
              className="w-full"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-sky-700 mb-1">
              Número Interior
            </label>
            <Input
              value={interiorNumber}
              onChange={(e) => setInteriorNumber(e.target.value)}
              placeholder="A"
              className="w-full"
            />
          </div>
        </div>

        {/* Código Postal Section */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-sky-700 mb-1">
              Código Postal *
            </label>
            <Input
              value={postalCode}
              onChange={(e) => handleCPSearch(e.target.value)}
              placeholder="01000"
              maxLength={5}
              className="w-full"
            />
            {isSearchingByCP && (
              <p className="text-xs text-sky-600 mt-1">Buscando colonias...</p>
            )}
          </div>

          {cpSearchResult && !cpSearchResult.error && (
            <div className="space-y-2">
              <label className="block text-sm font-medium text-sky-700">
                Selecciona tu colonia *
              </label>
              <div className="space-y-1">
                {cpSearchResult.codigo_postal.colonias.map((colonia, index) => (
                  <button
                    key={index}
                    onClick={() => selectFromCPResult(colonia)}
                    className={`w-full text-left p-3 text-sm rounded-lg border transition-colors ${
                      selectedColonia === colonia
                        ? 'bg-sky-50 border-sky-300 text-sky-700'
                        : 'hover:bg-sky-50 border-gray-300'
                    }`}
                  >
                    <div className="font-medium">{colonia}</div>
                    <div className="text-sky-600 text-xs">
                      {cpSearchResult.codigo_postal.municipio}, {cpSearchResult.codigo_postal.estado}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Show selected information */}
          {selectedColonia && cpSearchResult && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <p className="text-sm font-medium text-green-800 mb-1">Dirección seleccionada:</p>
              <p className="text-sm text-green-700">
                <span className="font-medium">{selectedColonia}</span><br />
                {cpSearchResult.codigo_postal.municipio}, {cpSearchResult.codigo_postal.estado}<br />
                CP: {cpSearchResult.codigo_postal.codigo_postal}
              </p>
            </div>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex justify-end space-x-3 pt-4 border-t">
          {onCancel && (
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isSubmitting}
            >
              Cancelar
            </Button>
          )}
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={!isFormValid() || isSubmitting}
            className="bg-sky-600 hover:bg-sky-700"
          >
            {isSubmitting ? "Guardando..." : "Confirmar Dirección"}
          </Button>
        </div>
      </div>
    </div>
  );
}