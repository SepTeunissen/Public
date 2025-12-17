# Modules for interacting with AT API
import requests
from colorama import Fore, Style
from datetime import datetime
import csv
import os

# fill thesevariables:
IncludedContractCategoryIDs = [28, 27]  #lijst met contractcategorieen die meegenomen moeten worden, in dit geval pab en msc, scheiden met ,
ExcludedServiceIds = [257]  # lijst met serviceids die uitgesloten moeten worden, in dit geval SMW, scheiden met ,
ExcludedCompanyIds = []  #voor het uitsluiten van bepaalde bedrijven, scheiden met ,
IndexPercentageChange = 3.1 #standaard percentage voor het wijzigen van de prijs
FardemIndexPercentageChange = 2.0 #specifiek percentage voor ....
FardemCompanyId = 974  #Companyid in Autotask voor ....
ChangeEffectiveDate = '2026-01-01'  #datum waarop de wijziging ingaat

#dev
ATUsername = ''
ATAPIIntegrationCode = ''
ATSecret = ''

#Prod
#ATUsername = ''
#ATAPIIntegrationCode = ''
#ATSecret = ''

SucceededChanges = []
SkippedChanges = []
RejectedChanges = []
FailedChanges = []

# Functions for the AT API
def getATCompanies():
    url = 'https://webservices19.autotask.net/atservicesrest/v1.0/Companies/query?search={"filter":[{"op":"eq","field":"isactive","value":true}]}'

    all_companies = []

    while url:
        response = requests.get(
            url=url,
            headers={
                'ApiIntegrationCode': ATAPIIntegrationCode,
                'UserName': ATUsername,
                'Secret': ATSecret,
                'Content-Type': 'application/json'
            }
        )
        
        
        data = response.json()

        all_companies.extend(data.get("items", []))

        page_info = data.get("pageDetails", {})
        url = page_info.get("nextPageUrl")

    return all_companies


def getCurrentCompanyActiveContracts(CompanyID):
    url = f'https://webservices19.autotask.net/atservicesrest/v1.0/Contracts/query?search={{"filter":[{{"op":"eq","field":"companyId","value":{CompanyID}}},{{"op":"eq","field":"status","value":1}}]}}'
    response = requests.get(
            url=url,
            headers={
                'ApiIntegrationCode': ATAPIIntegrationCode,
                'UserName': ATUsername,
                'Secret': ATSecret,
                'Content-Type': 'application/json'
            }
        )

    data = response.json()

    return data.get("items", [])


def getCurrentContractServices(ContractID):
    url = f'https://webservices19.autotask.net/atservicesrest/v1.0/ContractServices/query?search={{"filter":[{{"op":"eq","field":"contractID","value":{ContractID}}}]}}'
    response = requests.get(
            url=url,
            headers={
                'ApiIntegrationCode': ATAPIIntegrationCode,
                'UserName': ATUsername,
                'Secret': ATSecret,
                'Content-Type': 'application/json'
            }
        )

    data = response.json()

    return data.get("items", [])    


def setATContractServicePrice(AdjustedUnitPrice, ContractID, EffectiveDate, ServiceID):
    url = f'https://webservices19.autotask.net/atservicesrest/V1.0/ContractServiceAdjustments'
    response = requests.post(
            url=url,
            headers={
                'ApiIntegrationCode': ATAPIIntegrationCode,
                'UserName': ATUsername,
                'Secret': ATSecret,
                'Content-Type': 'application/json'
            },
            json={
                'adjustedUnitPrice': AdjustedUnitPrice,
                'contractID': ContractID,
                'effectiveDate': EffectiveDate,
                'serviceID': ServiceID

            }
        )

    try:
        body = response.json()
    except ValueError:
        body = response.text

    return response.status_code, body


def export_to_csv(data, filename):
    if not data:
        return

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

# run script
companies = getATCompanies()
cwd = os.getcwd()

company_index = 0


print(f"Found {len(companies)} active companies\n")
# over bedrijven loopen
for company in companies:
    company_index += 1
    print(
          "-------------------------------------\n"
          "-------------------------------------\n"
          f"Company index = {company_index},\n"
          f"Company ID: {company['id']},\n"
          f"companyName: {company['companyName']}\n"
        )


    if company['id'] in ExcludedCompanyIds:
        print(
              Fore.GREEN + 
              f"Company ID {company['id']} is in the excluded company IDs list, skipping to next company\n" 
              "Gegevens opgeslagen voor latere export.\n"
              + Style.RESET_ALL
              )
        
        SkippedChanges.append({
            'CompanyID': company['id'],
            'CompanyName': company['companyName'],
            'Reason': 'CompanyID was excluded'
        })
        continue

    else:
        contracts = getCurrentCompanyActiveContracts(company['id'])
        print(f"Found {len(contracts)} active contracts")

        if len(contracts) == 0:
            print(
                Fore.GREEN + 
                "No active contracts, skipping to next company\n" 
                "Gegevens opgeslagen voor latere export.\n"
                + Style.RESET_ALL
              )
            
            SkippedChanges.append({
                'CompanyID': company['id'],
                'CompanyName': company['companyName'],
                'Reason': 'No active contracts'
            })
            continue
        
        else:
            print("Processing contracts...\n")
            contract_index = 0

            # over contracten loopen
            for contract in contracts:
                contract_index += 1

                skip_contract = False

                contract_end = datetime.fromisoformat(
                    contract['endDate'].replace("Z", "+00:00")
                )
                change_date = datetime.fromisoformat(
                    f"{ChangeEffectiveDate}T00:00:00.000+00:00"
                )

                if contract_end < change_date:
                        print(
                            Fore.YELLOW + 
                            f"\nContract {contract['contractName']} loopt af op {contract['endDate']}, "
                            f"wat eerder is dan de ingangsdatum van de prijswijziging {ChangeEffectiveDate}.\n"
                            "Dit is de reden dat dit contract wordt overgeslagen\n"
                            "Gegevens opgeslagen voor latere export.\n"
                            + Style.RESET_ALL
                        )         
                        SkippedChanges.append({
                            'CompanyID': company['id'],
                            'CompanyName': company['companyName'],
                            'ContractID': contract['id'],
                            'ContractName': contract['contractName'],
                            'Reason': 'Contract ends before change effective date'
                        })
                        continue
                
                if contract['contractCategory'] not in IncludedContractCategoryIDs:
                    print(
                        Fore.YELLOW + 
                        f"\nContract {contract['contractName']} heeft contractcategorie ID "
                        f"{contract['contractCategory']}, wat niet in de lijst met mee te nemen "
                        f"contractcategorieën zit: {IncludedContractCategoryIDs}.\n"
                        "Dit is de reden dat dit contract wordt overgeslagen\n"
                        "Gegevens opgeslagen voor latere export.\n"
                        + Style.RESET_ALL
                    )         
                    SkippedChanges.append({
                        'CompanyID': company['id'],
                        'CompanyName': company['companyName'],
                        'ContractID': contract['id'],
                        'ContractName': contract['contractName'],
                        'Reason': 'Contract category ID not included'
                    })
                    continue

                print(
                    f"Contract index: {contract_index},\n"
                    f"Contract ID: {contract['id']},\n"
                    f"contractName: {contract['contractName']}\n"
                    )

                contractServices = getCurrentContractServices(contract['id'])
                print(f"Found {len(contractServices)} contract services")

                if len(contractServices) == 0:
                    print(
                        Fore.GREEN + 
                        "No contract services, skipping to next contract\n" 
                        "Gegevens opgeslagen voor latere export.\n"
                        + Style.RESET_ALL
                        )

                    SkippedChanges.append({
                        'CompanyID': company['id'],
                        'CompanyName': company['companyName'],
                        'ContractID': contract['id'],
                        'ContractName': contract['contractName'],
                        'Reason': 'No contract services'
                    })
                    continue

                else:
                    print("Processing contract services...\n")
                    service_index = 0
                    
                    # over contract services loopen
                    for service in contractServices:
                        service_index += 1
                        print(
                            f"Service index: {service_index},\n"
                            f"Contract Service ID: {service['serviceID']},\n"
                            f"serviceName: {service['invoiceDescription']},\n"
                            f"currentPrice: {service['unitPrice']}\n"
                            )

                        if service['serviceID'] in ExcludedServiceIds:
                            print(
                                Fore.GREEN + 
                                f"Service ID {service['serviceID']} is in the excluded service IDs list, skipping {service['invoiceDescription']}\n" 
                                "Gegevens opgeslagen voor latere export.\n"
                                + Style.RESET_ALL
                                )
                            
                            
                            SkippedChanges.append({
                                'CompanyID': company['id'],
                                'CompanyName': company['companyName'],
                                'ContractID': contract['id'],
                                'ContractName': contract['contractName'],
                                'ServiceID': service['serviceID'],
                                'ServiceName': service['invoiceDescription'],
                                'Reason': 'ServiceID was excluded'
                            })
                            continue

                        else:
                            if company['id'] == FardemCompanyId:
                                new_price = round(service['unitPrice'] * (1 + FardemIndexPercentageChange / 100), 2)
                                used_percentage = FardemIndexPercentageChange
                            else:
                                new_price = round(service['unitPrice'] * (1 + IndexPercentageChange / 100), 2)
                                used_percentage = IndexPercentageChange

                            while True:
                                approve = input(
                                    f"\nHee Mike!\n Voor {company['companyName']} en contract {contract['contractName']} "
                                    f"gaan we de prijs van service '{service['invoiceDescription']}'\naanpassen "
                                    f"van {service['unitPrice']} naar {new_price}, omdat de index {used_percentage} is gebruikt\n"
                                    "Geef een 'y' als dit akkoord is en een 'n' als dit niet akkoord is:\n"
                                ).strip().lower()

                                if approve == 'y':
                                    print(f"Prijs aanpassen met de volgende gegevens:\n"
                                          f"AdjustedUnitPrice: {new_price}\n"
                                          f"ContractID: {contract['id']}\n"
                                          f"EffectiveDate: {ChangeEffectiveDate}\n"
                                          f"ServiceID: {service['serviceID']}\n"
                                          )
                                    
                                    status_code, response_body = setATContractServicePrice(
                                        AdjustedUnitPrice=new_price,
                                        ContractID=contract['id'],
                                        EffectiveDate=ChangeEffectiveDate,
                                        ServiceID=service['serviceID']
                                    )

                                    if status_code not in (200, 201):
                                        error_message = (
                                            response_body.get('error', {}).get('message')
                                            if isinstance(response_body, dict)
                                            else response_body
                                        )

                                        print(
                                            Fore.RED + 
                                            f"Fout bij het aanpassen van de prijs: {error_message}\n" 
                                            "Gegevens opgeslagen voor latere export.\n"
                                            + Style.RESET_ALL
                                            )
                                        

                                        FailedChanges.append({
                                            'CompanyID': company['id'],
                                            'CompanyName': company['companyName'],
                                            'ContractID': contract['id'],
                                            'ContractName': contract['contractName'],
                                            'ServiceID': service['serviceID'],
                                            'ServiceName': service['invoiceDescription'],
                                            'CurrentPrice': service['unitPrice'],
                                            'ProposedPrice': new_price,
                                            'Reason': "error tijdens het verwerken van het verschil"
                                        })
                                    else:
                                        print(
                                            Fore.GREEN + 
                                            f"Prijs succesvol aangepast voor service '{service['invoiceDescription']}' van contract '{contract['contractName']}'\nNieuwe prijs: {new_price}\n" 
                                            "Gegevens opgeslagen voor latere export.\n"
                                            + Style.RESET_ALL
                                            )

                                        SucceededChanges.append({
                                            'CompanyID': company['id'],
                                            'CompanyName': company['companyName'],
                                            'ContractID': contract['id'],
                                            'ContractName': contract['contractName'],
                                            'ServiceID': service['serviceID'],
                                            'ServiceName': service['invoiceDescription'],
                                            'OldPrice': service['unitPrice'],
                                            'NewPrice': new_price
                                        })

                                    break

                                elif approve == 'n':
                                    print(
                                        Fore.YELLOW + 
                                        f"Prijsaanpassing overgeslagen op verzoek\n" 
                                        "Gegevens opgeslagen voor latere export.\n"
                                        + Style.RESET_ALL
                                        )

                                    RejectedChanges.append({
                                        'CompanyID': company['id'],
                                        'CompanyName': company['companyName'],
                                        'ContractID': contract['id'],
                                        'ContractName': contract['contractName'],
                                        'ServiceID': service['serviceID'],
                                        'ServiceName': service['invoiceDescription'],
                                        'CurrentPrice': service['unitPrice'],
                                        'ProposedPrice': new_price,
                                        'Reason': 'Price change rejected by user'
                                    })
                                    break

                                else:
                                    print(
                                        Fore.YELLOW + "Ongeldige invoer, probeer opnieuw.\n" + Style.RESET_ALL
                                        )
                                    

print(
    "\n-------------------------------------\nScript voltooid.\n"
    f"Afgewezen prijswijzigingen: {len(RejectedChanges)}\n"
    f"Mislukte prijswijzigingen: {len(FailedChanges)}\n"
    f"Geslaagde prijswijzigingen: {len(SucceededChanges)}\n"
    f"Overgeslagen prijswijzigingen: {len(SkippedChanges)}\n"
    "wijzig deze zelf in Autotask.\n"
)

if RejectedChanges:
    print("Details van afgewezen prijswijzigingen zijn geëxporteerd naar CSV bestand. te vinden in de werkmap van dit script.")
    export_to_csv(RejectedChanges,  os.path.join(cwd, f"rejected_AtPrice_changes.csv"))

if FailedChanges:
    print("Details van mislukte prijswijzigingen zijn geëxporteerd naar CSV bestand. te vinden in de werkmap van dit script.")
    export_to_csv(FailedChanges,    os.path.join(cwd, f"failed_AtPrice_changes.csv"))

if SucceededChanges:
    print("Details van geslaagde prijswijzigingen zijn geëxporteerd naar CSV bestand. te vinden in de werkmap van dit script.")
    export_to_csv(SucceededChanges, os.path.join(cwd, f"succeeded_AtPrice_changes.csv"))

if SkippedChanges:
    print("Details van overgeslagen prijswijzigingen zijn geëxporteerd naar CSV bestand. te vinden in de werkmap van dit script.")
    export_to_csv(SkippedChanges,   os.path.join(cwd, f"skipped_AtPrice_changes.csv"))

print(
    Fore.GREEN + f"\nEinde van script, bedankt Mike!"
    )