#include "OWGameFlow.h"
#include "OWExplorerCharacter.h"
#include "OWPlayerController.h"

AOWGameMode::AOWGameMode()
{
    PlayerControllerClass = AOWPlayerController::StaticClass();
    DefaultPawnClass = AOWExplorerCharacter::StaticClass();
}

void AOWGameMode::InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage)
{
    if (MapName.Contains(TEXT("L_Menu_V1")))
        DefaultPawnClass = nullptr;
    Super::InitGame(MapName, Options, ErrorMessage);
}
