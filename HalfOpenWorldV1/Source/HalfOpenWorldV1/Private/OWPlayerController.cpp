#include "OWPlayerController.h"

#include "OWGameFlow.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/GameUserSettings.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/SBoxPanel.h"

const FString AOWPlayerController::SaveSlot = TEXT("HalfOpenWorldV1_Player");

bool AOWPlayerController::IsMenuLevel() const
{
    return GetWorld() && GetWorld()->GetMapName().Contains(TEXT("L_Menu_V1"));
}

void AOWPlayerController::BeginPlay()
{
    Super::BeginPlay();
    if (IsMenuLevel())
    {
        ShowMainMenu();
    }
    else
    {
        bShowMouseCursor = false;
        SetInputMode(FInputModeGameOnly());
        RestoreIfRequested();
        UE_LOG(LogTemp, Display, TEXT("[HalfOpenWorldV1] World ready. WASD / mouse / Space / Shift / Esc."));
    }
}

void AOWPlayerController::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    RemoveMenu();
    Super::EndPlay(EndPlayReason);
}

void AOWPlayerController::SetupInputComponent()
{
    Super::SetupInputComponent();
    FInputKeyBinding& PauseBinding = InputComponent->BindKey(EKeys::Escape, IE_Pressed, this,
        &AOWPlayerController::TogglePause);
    PauseBinding.bExecuteWhenPaused = true;
}

void AOWPlayerController::OnPossess(APawn* InPawn)
{
    Super::OnPossess(InPawn);
    RestoreIfRequested();
}

void AOWPlayerController::RestoreIfRequested()
{
    UOWGameInstance* Session = GetGameInstance<UOWGameInstance>();
    if (!Session || !Session->bRestoreOnNextWorld || !GetPawn()) return;
    Session->bRestoreOnNextWorld = false;
    UOWSaveGame* Save = Cast<UOWSaveGame>(UGameplayStatics::LoadGameFromSlot(SaveSlot, 0));
    if (Save)
    {
        GetPawn()->SetActorLocation(Save->PlayerLocation);
        SetControlRotation(Save->PlayerRotation);
        UE_LOG(LogTemp, Display, TEXT("[HalfOpenWorldV1] Save restored."));
    }
}

void AOWPlayerController::RemoveMenu()
{
    if (ActiveMenu.IsValid() && GEngine && GEngine->GameViewport)
        GEngine->GameViewport->RemoveViewportWidgetContent(ActiveMenu.ToSharedRef());
    ActiveMenu.Reset();
}

void AOWPlayerController::AddButton(TSharedRef<SVerticalBox> Rows, const FString& Caption,
    FOnClicked Clicked, bool bEnabled)
{
    Rows->AddSlot().AutoHeight().Padding(0.f, 5.f)
    [
        SNew(SButton)
        .IsEnabled(bEnabled)
        .OnClicked(Clicked)
        .ContentPadding(FMargin(18.f, 12.f))
        .ButtonColorAndOpacity(FLinearColor(0.19f, 0.16f, 0.12f, 1.f))
        [
            SNew(STextBlock)
            .Text(FText::FromString(Caption))
            .ColorAndOpacity(FSlateColor(FLinearColor(0.96f, 0.84f, 0.61f)))
            .Font(FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 19))
        ]
    ];
}

void AOWPlayerController::BuildPanel(const FString& Heading, const FString& Description,
    TSharedRef<SVerticalBox> Rows)
{
    RemoveMenu();
    if (!GEngine || !GEngine->GameViewport) return;

    TSharedRef<SWidget> Root = SNew(SOverlay)
        + SOverlay::Slot()
        [
            SNew(SBorder)
            .BorderImage(FCoreStyle::Get().GetBrush(TEXT("WhiteBrush")))
            .BorderBackgroundColor(FLinearColor(0.01f, 0.015f, 0.02f, 0.55f))
        ]
        + SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Center).Padding(FMargin(64.f, 0.f))
        [
            SNew(SBox).WidthOverride(470.f)
            [
                SNew(SBorder).Padding(FMargin(30.f, 28.f))
                .BorderImage(FCoreStyle::Get().GetBrush(TEXT("WhiteBrush")))
                .BorderBackgroundColor(FLinearColor(0.045f, 0.055f, 0.064f, 0.98f))
                [
                    SNew(SVerticalBox)
                    + SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 10.f)
                    [
                        SNew(STextBlock)
                        .Text(FText::FromString(Heading))
                        .ColorAndOpacity(FSlateColor(FLinearColor(0.91f, 0.72f, 0.38f)))
                        .Font(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 29))
                    ]
                    + SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 23.f)
                    [
                        SNew(STextBlock)
                        .Text(FText::FromString(Description))
                        .ColorAndOpacity(FSlateColor(FLinearColor(0.78f, 0.80f, 0.81f)))
                        .AutoWrapText(true)
                    ]
                    + SVerticalBox::Slot().AutoHeight()[Rows]
                    + SVerticalBox::Slot().AutoHeight().Padding(0.f, 24.f, 0.f, 0.f)
                    [
                        SNew(STextBlock)
                        .Text(FText::FromString(TEXT("V1  /  ASSINADO: SHOKK")))
                        .ColorAndOpacity(FSlateColor(FLinearColor(0.65f, 0.52f, 0.31f)))
                    ]
                ]
            ]
        ];
    ActiveMenu = Root;
    GEngine->GameViewport->AddViewportWidgetContent(Root, 50);
    bShowMouseCursor = true;
    SetInputMode(FInputModeGameAndUI().SetWidgetToFocus(Root).SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock));
}

void AOWPlayerController::ShowMainMenu()
{
    TSharedRef<SVerticalBox> Rows = SNew(SVerticalBox);
    AddButton(Rows, TEXT("NOVO JOGO"), FOnClicked::CreateUObject(this, &AOWPlayerController::StartNewGame));
    AddButton(Rows, TEXT("CONTINUAR"), FOnClicked::CreateUObject(this, &AOWPlayerController::ContinueGame),
        UGameplayStatics::DoesSaveGameExist(SaveSlot, 0));
    AddButton(Rows, TEXT("CONFIGURACOES"), FOnClicked::CreateUObject(this, &AOWPlayerController::OpenSettings));
    AddButton(Rows, TEXT("SAIR"), FOnClicked::CreateUObject(this, &AOWPlayerController::ExitGame));
    BuildPanel(TEXT("HALF OPEN WORLD"), TEXT("Um novo caminho. Protótipo jogável de shokk."), Rows);
}

void AOWPlayerController::ShowPauseMenu()
{
    TSharedRef<SVerticalBox> Rows = SNew(SVerticalBox);
    AddButton(Rows, TEXT("VOLTAR AO JOGO"), FOnClicked::CreateUObject(this, &AOWPlayerController::ResumeGame));
    AddButton(Rows, TEXT("SALVAR E VOLTAR AO MENU"), FOnClicked::CreateUObject(this, &AOWPlayerController::SaveAndReturn));
    AddButton(Rows, TEXT("CONFIGURACOES"), FOnClicked::CreateUObject(this, &AOWPlayerController::OpenSettings));
    AddButton(Rows, TEXT("SAIR"), FOnClicked::CreateUObject(this, &AOWPlayerController::ExitGame));
    BuildPanel(TEXT("PAUSA"), TEXT("WASD mover  |  Mouse olhar  |  Espaco pular  |  Shift correr"), Rows);
}

void AOWPlayerController::ShowSettingsMenu()
{
    TSharedRef<SVerticalBox> Rows = SNew(SVerticalBox);
    AddButton(Rows, TEXT("QUALIDADE BAIXA (RECOMENDADA)"), FOnClicked::CreateUObject(this, &AOWPlayerController::QualityLow));
    AddButton(Rows, TEXT("QUALIDADE MEDIA"), FOnClicked::CreateUObject(this, &AOWPlayerController::QualityMedium));
    AddButton(Rows, TEXT("VOLTAR"), FOnClicked::CreateUObject(this, &AOWPlayerController::BackFromSettings));
    BuildPanel(TEXT("CONFIGURACOES"), TEXT("As mudancas de qualidade sao salvas no PC."), Rows);
}

FReply AOWPlayerController::StartNewGame()
{
    if (UOWGameInstance* Session = GetGameInstance<UOWGameInstance>()) Session->bRestoreOnNextWorld = false;
    UGameplayStatics::OpenLevel(this, FName(TEXT("L_World_V1")));
    return FReply::Handled();
}

FReply AOWPlayerController::ContinueGame()
{
    if (!UGameplayStatics::DoesSaveGameExist(SaveSlot, 0)) return FReply::Handled();
    if (UOWGameInstance* Session = GetGameInstance<UOWGameInstance>()) Session->bRestoreOnNextWorld = true;
    UGameplayStatics::OpenLevel(this, FName(TEXT("L_World_V1")));
    return FReply::Handled();
}

FReply AOWPlayerController::ResumeGame()
{
    RemoveMenu();
    bPauseOpen = false;
    UGameplayStatics::SetGamePaused(this, false);
    bShowMouseCursor = false;
    SetInputMode(FInputModeGameOnly());
    return FReply::Handled();
}

FReply AOWPlayerController::SaveAndReturn()
{
    if (APawn* ControlledPawn = GetPawn())
    {
        UOWSaveGame* Save = Cast<UOWSaveGame>(UGameplayStatics::CreateSaveGameObject(UOWSaveGame::StaticClass()));
        Save->PlayerLocation = ControlledPawn->GetActorLocation();
        Save->PlayerRotation = GetControlRotation();
        if (!UGameplayStatics::SaveGameToSlot(Save, SaveSlot, 0))
            UE_LOG(LogTemp, Error, TEXT("[HalfOpenWorldV1] Could not save progress."));
    }
    UGameplayStatics::SetGamePaused(this, false);
    UGameplayStatics::OpenLevel(this, FName(TEXT("L_Menu_V1")));
    return FReply::Handled();
}

FReply AOWPlayerController::OpenSettings() { ShowSettingsMenu(); return FReply::Handled(); }
FReply AOWPlayerController::BackFromSettings()
{
    if (IsMenuLevel()) ShowMainMenu(); else ShowPauseMenu();
    return FReply::Handled();
}

void AOWPlayerController::SetQuality(int32 Level)
{
    if (GEngine && GEngine->GetGameUserSettings())
    {
        UGameUserSettings* Settings = GEngine->GetGameUserSettings();
        Settings->SetOverallScalabilityLevel(Level);
        Settings->ApplyNonResolutionSettings();
        Settings->SaveSettings();
    }
    ShowSettingsMenu();
}

FReply AOWPlayerController::QualityLow() { SetQuality(0); return FReply::Handled(); }
FReply AOWPlayerController::QualityMedium() { SetQuality(1); return FReply::Handled(); }
FReply AOWPlayerController::ExitGame()
{
    UGameplayStatics::SetGamePaused(this, false);
    UKismetSystemLibrary::QuitGame(this, this, EQuitPreference::Quit, false);
    return FReply::Handled();
}

void AOWPlayerController::TogglePause()
{
    if (IsMenuLevel()) return;
    if (bPauseOpen) ResumeGame();
    else
    {
        bPauseOpen = true;
        UGameplayStatics::SetGamePaused(this, true);
        ShowPauseMenu();
    }
}
