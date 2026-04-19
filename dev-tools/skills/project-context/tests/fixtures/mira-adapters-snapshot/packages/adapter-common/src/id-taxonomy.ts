// Helper for ID taxonomy contract
export function makeIdHelper(prefix: string) {
  return (id: string) => `${prefix}:${id}`;
}

export const patientIdHelper = makeIdHelper("patient");
export const visitIdHelper = makeIdHelper("visit");
