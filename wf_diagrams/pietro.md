# pietro Flowchart

```mermaid
flowchart TD
    A["Admin (Azienda di commercialisti)"] --> B{"Crea/Modifica Promemoria"} & C{"Sistema automatico (Cron Job)"} & D["Cliente finale"]
    B --> B1["Definisce: <br>Tipo (scadenza, pagamento), <br>Data del mese, <br>Messaggio, <br>Canale (WhatsApp/Email), <br>Link Fattura/Pagamento"] & B2["Associa Clienti <br>(preimportati o aggiunti manualmente)"]
    C --> C1["Ogni giorno controlla i promemoria con data = giorno corrente"] & C15["Possibilità di trigger manuale (invio anticipato)"]
    C1 --> C11{"Per ogni promemoria scaduto o in scadenza"}
    C11 --> C12["Genera notifica per ogni cliente associato"]
    C12 --> C121["Email<br>Invia messaggio con link fattura/pagamento (Stripe)"] & C122["WhatsApp<br>Invia messaggio con link fattura/pagamento (Stripe)"]
    C12 -.-> n1(("ERROR HANDLING<br>(Errore Invio Notifica)"))
    D --> D1["Riceve notifica (Email/WhatsApp)"] & D2["Storico notifiche/pagamenti visibile nel portale admin"]
    D1 --> D11["Visualizza fattura (link allegato)"] & D12["Effettua pagamento (link Stripe)"]
    C122 --> C13["Registra lo storico delle notifiche inviate"]
    C122 -.-> n2["ERROR HANDLING<br>(Errore Pagamento)"]
    C121 -.-> n2
    C13 --> C14["Aggiorna stato promemoria <br>(eseguito)"]
    C121 --> C13
