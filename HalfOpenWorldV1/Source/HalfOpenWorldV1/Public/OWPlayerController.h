#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "Widgets/Input/SButton.h"
#include "OWPlayerController.generated.h"

class SVerticalBox;
class SWidget;

UCLASS()
class HALFOPENWORLDV1_API AOWPlayerController : public APlayerController
{
    GENERATED_BODY()
public:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void SetupInputComponent() override;
    virtual void OnPossess(APawn* InPawn) override;

private:
    static const FString SaveSlot;
    TSharedPtr<SWidget> ActiveMenu;
    bool bPauseOpen = false;

    bool IsMenuLevel() const;
    void RemoveMenu();
    void ShowMainMenu();
    void ShowPauseMenu();
    void ShowSettingsMenu();
    void BuildPanel(const FString& Heading, const FString& Description, TSharedRef<SVerticalBox> Rows);
    void AddButton(TSharedRef<SVerticalBox> Rows, const FString& Caption, FOnClicked Clicked, bool bEnabled = true);
    void RestoreIfRequested();
    void TogglePause();
    void SetQuality(int32 Level);

    FReply StartNewGame();
    FReply ContinueGame();
    FReply ResumeGame();
    FReply SaveAndReturn();
    FReply OpenSettings();
    FReply BackFromSettings();
    FReply QualityLow();
    FReply QualityMedium();
    FReply ExitGame();
};
