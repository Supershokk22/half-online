#pragma once

#include "CoreMinimal.h"
#include "Engine/GameInstance.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/SaveGame.h"
#include "OWGameFlow.generated.h"

UCLASS()
class HALFOPENWORLDV1_API UOWGameInstance : public UGameInstance
{
    GENERATED_BODY()
public:
    bool bRestoreOnNextWorld = false;
};

UCLASS()
class HALFOPENWORLDV1_API UOWSaveGame : public USaveGame
{
    GENERATED_BODY()
public:
    UPROPERTY() FVector PlayerLocation = FVector::ZeroVector;
    UPROPERTY() FRotator PlayerRotation = FRotator::ZeroRotator;
};

UCLASS()
class HALFOPENWORLDV1_API AOWGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    AOWGameMode();
    virtual void InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage) override;
};
